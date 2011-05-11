import ast
import unittest
import types
import time
import threading
import ctypes
from os import path
import imp

from mutpy import mutator, view


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
        return (self.killed_mutants / (self.all_mutants - self.incompetent_mutants)) * 100
    
    def inc_all(self):
        self.all_mutants += 1
        
    def inc_killed(self):
        self.killed_mutants += 1
        
    def inc_timeout(self):
        self.timeout_mutants += 1
        
    def inc_incompetent(self):
        self.incompetent_mutants += 1
    
            
class MutationController(view.ViewNotifier):
    
    def __init__(self, mutation_cfg, views=None):
        super().__init__(views)
        self.target_name = mutation_cfg.target
        self.tests_name = mutation_cfg.test
        self.mutation_cfg = mutation_cfg
        self.loader = ModulesLoader(self.target_name, self.tests_name)
        
    def run(self):
        start_time = time.time()
        self.notify_initialize(self.mutation_cfg)
        target_module, to_mutate = self.loader.load_target()
        target_ast = self.create_target_ast(target_module)
        
        try:
            test_modules = self.load_and_check_tests()
            self.notify_passed(test_modules)
            mutant_generator = self.create_mutator(target_ast)
            score = MutationScore()
            self.notify_start()
            
            for op, lineno, mutant_ast in mutant_generator.mutate():
                self.notify_mutation(op, lineno, mutant_ast)
                score.inc_all()
                mutant_module = self.create_mutant_module(target_module, mutant_ast)
                self.run_tests_with_mutant(test_modules, mutant_module, score)
                    
            self.notify_end(score, time.time() - start_time)
        except TestsFailAtOriginal as error:
            self.notify_failed(error.result)        

    def load_target_module(self):
        if self.target_name.endswith('.py'):
            self.target_name = self.target_name[:-3]
        return __import__(self.target_name, globals(), locals())
        
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
            suite.run(result)
            duration = time.time() - start
            if result.wasSuccessful():
                test_modules.append((test_module, target_test, duration))
            else:
                raise TestsFailAtOriginal(result)
            
        return test_modules
        
    def create_mutator(self, target_ast):
        return mutator.Mutator(target_ast, self.mutation_cfg)
        
    def create_mutant_module(self, target_module, mutant_ast):
        mutant_code = compile(mutant_ast, 'mutant', 'exec')
        mutant_module = types.ModuleType(target_module.__name__.split('.')[-1])
        exec(mutant_code, mutant_module.__dict__)
        return mutant_module
        
    def run_tests_with_mutant(self, tests_modules, mutant_module, score):
        suite = unittest.TestSuite()
        total_duration = 0
        for test_module, target_test, duration in tests_modules:
            test_module.__dict__[mutant_module.__name__] = mutant_module
            if target_test:
                suite.addTests(unittest.TestLoader().loadTestsFromName(target_test, test_module))
            else:
                suite.addTests(unittest.TestLoader().loadTestsFromModule(test_module))
            total_duration += duration
            
        result = unittest.TestResult()
        result.failfast = True
        start = time.time()
        runner_thread = KillableThread(target=lambda: suite.run(result))
        runner_thread.start()
        live_time = self.mutation_cfg.timeout_factor * total_duration if total_duration > 1 else 1
        runner_thread.join(live_time)
        mutant_duration = time.time() - start
        
        if runner_thread.is_alive():
            runner_thread.kill()
            self.notify_timeout()
            score.inc_timeout()
        elif result.errors:
            self.notify_error()
            score.inc_incompetent()
        elif result.wasSuccessful():
            self.notify_survived(mutant_duration)
        else:       
            self.notify_killed(mutant_duration)
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
            try:
                module_detalis = imp.find_module(module_name, search_path)
                module = imp.load_module(module_name, *module_detalis)
            except ImportError:
                raise ModulesLoaderException(name)
            
            return module, None
    
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
        return self.load(self.target)
    
    def load_tests(self):
        return [self.load(test) for test in self.tests]
    
