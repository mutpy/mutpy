import ast
import unittest
import types
import time
import threading
import ctypes
from os import path
import imp
import sys

from mutpy import views
from unittest.result import TestResult
from _pyio import StringIO

class TestsFailAtOriginal(Exception):
    
    def __init__(self, result=None):
        self.result = result


class ModulesLoaderException(Exception):
    
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return "cant't load {}".format(self.name)


class MutationScore:
    
    def __init__(self, all_mutants=0, killed_mutants=0, timeout_mutants=0, incompetent_mutants=0):
        self.all_mutants = all_mutants
        self.killed_mutants = killed_mutants
        self.timeout_mutants = timeout_mutants
        self.incompetent_mutants = incompetent_mutants
        
    def count(self):
        bottom = self.all_mutants - self.incompetent_mutants
        return ((self.killed_mutants / bottom) * 100) if bottom else 0
    
    def inc_all(self):
        self.all_mutants += 1
        
    def inc_killed(self):
        self.killed_mutants += 1
        
    def inc_timeout(self):
        self.timeout_mutants += 1
        
    def inc_incompetent(self):
        self.incompetent_mutants += 1
    
            
class MutationController(views.ViewNotifier):
    
    def __init__(self, loader, views, mutant_generator, timeout_factor, disable_stdout=False):
        super().__init__(views)
        self.loader = loader
        self.mutant_generator = mutant_generator
        self.timeout_factor = timeout_factor
        self.stdout_manager = StdoutManager(disable_stdout)
        
    def run(self):
        start_time = time.time()
        self.notify_initialize(self.loader.target, self.loader.tests)
        
        try:
            target_module, to_mutate = self.loader.load_target()
            target_ast = self.create_target_ast(target_module)
            test_modules = self.load_and_check_tests()
            self.notify_passed(test_modules)
            score = MutationScore()
            self.notify_start()
            
            for op, lineno, mutant_ast in self.mutant_generator.mutate(target_ast, to_mutate):
                self.notify_mutation(op, lineno, mutant_ast)
                score.inc_all()
                mutant_module = self.create_mutant_module(target_module, mutant_ast)
                if mutant_module:
                    self.run_tests_with_mutant(test_modules, mutant_module, score)
                else:
                    score.inc_incompetent()
                    self.notify_error()
                    
            self.notify_end(score, time.time() - start_time)
        except TestsFailAtOriginal as error:
            self.notify_failed(error.result)
        except ModulesLoaderException as error:
            self.notify_cant_load(error.name)
        except KeyboardInterrupt:
            self.notify_end(score, time.time() - start_time)        
        
    def create_target_ast(self, target_module):
        with open(target_module.__file__) as target_file: 
            return ast.parse(target_file.read())
        
    def load_and_check_tests(self):
        test_modules = []
        for test_module, target_test in self.loader.load_tests():
            if target_test:
                suite = unittest.TestLoader().loadTestsFromName(target_test, test_module)
            else:
                suite = unittest.TestLoader().loadTestsFromModule(test_module)
            result = unittest.TestResult()
            start = time.time()
            self.stdout_manager.disable_stdout()
            suite.run(result)
            self.stdout_manager.enable_stdout()
            duration = time.time() - start
            if result.wasSuccessful():
                test_modules.append((test_module, target_test, duration))
            else:
                raise TestsFailAtOriginal(result)
            
        return test_modules
        
    def create_mutant_module(self, target_module, mutant_ast):
        try:
            mutant_code = compile(mutant_ast, 'mutant', 'exec')
            mutant_module = types.ModuleType(target_module.__name__.split('.')[-1])
            self.stdout_manager.disable_stdout()
            exec(mutant_code, mutant_module.__dict__)
            self.stdout_manager.enable_stdout()
        except Exception:
            return None
        
        return mutant_module
        
    def create_test_suite(self, tests_modules, mutant_module):
        suite = unittest.TestSuite()
        total_duration = 0
        for test_module, target_test, duration in tests_modules:
            self.inject_mutant(mutant_module, test_module)
            if target_test:
                suite.addTests(unittest.TestLoader().loadTestsFromName(target_test, test_module))
            else:
                suite.addTests(unittest.TestLoader().loadTestsFromModule(test_module))
            total_duration += duration
        
        return suite, total_duration
    
    def inject_mutant(self, mutant_module, test_module):
        if mutant_module.__name__ in test_module.__dict__: 
            old_module = test_module.__dict__[mutant_module.__name__]
            mutant_module.__file__ = old_module.__file__
            test_module.__dict__[mutant_module.__name__] = mutant_module
        else:
            mutant_set = set(mutant_module.__dict__)
            test_set = set(test_module.__dict__)
            intersection = (mutant_set & test_set) - {'__builtins__', '__name__', '__doc__'}
            intersection = {artefact for artefact in intersection if not imp.is_builtin(artefact)}
            for to_inject in intersection:
                test_module.__dict__[to_inject] = mutant_module.__dict__[to_inject]
            

    def run_tests_with_mutant(self, tests_modules, mutant_module, score):
        
        suite, total_duration = self.create_test_suite(tests_modules, mutant_module)
        result = CustomTestResult()
        result.failfast = True
        start = time.time()
        runner_thread = KillableThread(target=lambda: suite.run(result))
        self.stdout_manager.disable_stdout()
        runner_thread.start()
        live_time = self.timeout_factor * total_duration if total_duration > 1 else 1
        runner_thread.join(live_time)
        self.stdout_manager.enable_stdout()
        mutant_duration = time.time() - start
        if runner_thread.is_alive():
            runner_thread.kill()
            self.notify_timeout()
            score.inc_timeout()
        elif result.type_error:
            self.notify_error()
            score.inc_incompetent()
        elif result.wasSuccessful():
            self.notify_survived(mutant_duration)
        else:
            if result.failures:
                killer = result.failures[0][0]
            elif result.errors:
                killer = result.errors[0][0]
            self.notify_killed(mutant_duration, killer)
            score.inc_killed()
        
      
class KillableThread(threading.Thread):
    
    def kill(self):
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(SystemExit))
            if res == 0:
                raise ValueError("Invalid thread id.")
            elif res != 1:
                raise SystemError("Thread killing failed.")


class ModulesLoader:
    
    def __init__(self, target, tests):
        self.target = target
        self.tests = tests

    def load(self, name):
        if self.is_file(name):
            return self.load_file(name)
        else:              
            return self.load_module(name)
        
    def is_file(self, name):
        return name.endswith('.py')
        
    def load_file(self, name):
            search_path = [path.dirname(name)]
            file_name = path.basename(name)
            module_name = file_name[:-3]
            self.extend_path(name)
            try:
                module_detalis = imp.find_module(module_name, search_path)
                module = imp.load_module(module_name, *module_detalis)
                module_detalis[0].close()
            except ImportError:
                raise ModulesLoaderException(name)
            
            return module, None
        
    def extend_path(self, name):
        p = path.dirname(name)
        sys.path = [p] + sys.path
        
        while path.exists(p + '/__init__.py'):
            p = path.split(p)[0]
            sys.path = [p] + sys.path
    
    def load_module(self, name):
            parts = name.split('.')
            to_mutate = []
            while True:
                if not parts:
                    raise ModulesLoaderException(name)
                try:
                    module = __import__('.'.join(parts))
                    break
                except ImportError:
                    to_mutate = [parts.pop()] + to_mutate
            
            for part in parts[1:]:
                module = getattr(module, part)
            
            attr = module
            for part in to_mutate:
                if hasattr(attr, part):
                    attr = getattr(attr, part)
                else:
                    raise ModulesLoaderException(name)
            
            return module, '.'.join(to_mutate) if to_mutate else None
        
    def load_target(self):
        loaded_target = self.load(self.target)
        return loaded_target
    
    def load_tests(self):
        return [self.load(test) for test in self.tests]
    
class Mutator:
    
    def __init__(self, operators):
        self.operators = operators
    
    def add_operator(self, operator):
        self.operators.append(operator)
        
    def mutate(self, target_ast, to_mutate):
        for op in self.operators:
            for mutant, lineno in op().mutate(target_ast, to_mutate):
                yield op, lineno, mutant

    
class StdoutManager:
    
    def __init__(self, disable=True):
        self.disable = disable
        
    def disable_stdout(self):
        if self.disable:
            sys.stdout = StringIO()
        
    def enable_stdout(self):
        sys.stdout = sys.__stdout__


class CustomTestResult(TestResult):
    
    def __init__(self, *args, **kwargs):
        self.type_error = None
        super(CustomTestResult, self).__init__(*args, **kwargs)
    
    def addError(self, test, err):
        if err[0] == TypeError:
            self.type_error = err
        else:
            super(CustomTestResult, self).addError(test, err)