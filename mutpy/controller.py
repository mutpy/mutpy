from os import path
import ast
import types
import unittest
from mutpy import views, utils


class TestsFailAtOriginal(Exception):

    def __init__(self, result=None):
        self.result = result


class MutationScore:

    def __init__(self):
        self.killed_mutants = 0 
        self.timeout_mutants = 0 
        self.incompetent_mutants = 0 
        self.survived_mutants = 0

    def count(self):
        bottom = self.all_mutants - self.incompetent_mutants
        return (((self.killed_mutants + self.timeout_mutants) / bottom) * 100) if bottom else 0

    def inc_killed(self):
        self.killed_mutants += 1

    def inc_timeout(self):
        self.timeout_mutants += 1

    def inc_incompetent(self):
        self.incompetent_mutants += 1

    def inc_survived(self):
        self.survived_mutants += 1

    @property
    def all_mutants(self):
        return self.killed_mutants + self.timeout_mutants + self.incompetent_mutants + self.survived_mutants


class MutationController(views.ViewNotifier):

    def __init__(self, target_loader, test_loader, views, mutant_generator, 
                    timeout_factor=5, disable_stdout=False):
        super().__init__(views)
        self.target_loader = target_loader
        self.test_loader = test_loader
        self.mutant_generator = mutant_generator
        self.timeout_factor = timeout_factor
        self.stdout_manager = utils.StdoutManager(disable_stdout)

    def run(self):
        self.notify_initialize(self.target_loader.names, self.test_loader.names)
        try:
            score, time_reg = self.run_mutation()
            self.notify_end(score, time_reg)
        except TestsFailAtOriginal as error:
            self.notify_original_tests_fail(error.result)
        except utils.ModulesLoaderException as error:
            self.notify_cant_load(error.name)

    def run_mutation(self):
        try:
            time_reg = utils.TimeRegister()
            test_modules = self.load_and_check_tests()
            score = MutationScore()

            self.notify_passed(test_modules)
            self.notify_start()

            for target_module, to_mutate in self.target_loader.load():
                mutate_time_reg = self.mutate_module(target_module, to_mutate, test_modules, score)
                time_reg.add(mutate_time_reg)

        except KeyboardInterrupt:
            pass
            
        time_reg.stop()
        return score, time_reg

    def load_and_check_tests(self):
        test_modules = []
        for test_module, target_test in self.test_loader.load():
            result, duration = self.run_test(test_module, target_test)
            if result.wasSuccessful():
                test_modules.append((test_module, target_test, duration))
            else:
                raise TestsFailAtOriginal(result)

        return test_modules

    def run_test(self, test_module, target_test):
        if target_test:
            suite = unittest.TestLoader().loadTestsFromName(target_test, test_module)
        else:
            suite = unittest.TestLoader().loadTestsFromModule(test_module)
        result = unittest.TestResult()
        time_reg = utils.TimeRegister() 
        self.stdout_manager.disable_stdout()
        suite.run(result)
        self.stdout_manager.enable_stdout()
        time_reg.stop()
        duration = time_reg.main_task
        return result, duration

    def mutate_module(self, target_module, to_mutate, test_modules, score):
        time_reg = utils.TimeRegister()
        time_reg.start('generate_ast')
        target_ast = self.create_target_ast(target_module)
        time_reg.stop_last()
        filename = path.basename(target_module.__file__)
        inside_time_reg = utils.TimeRegister('mutate_ast_loop')
        for op, lineno, mutant_ast, mutate_time_reg in self.mutant_generator.mutate(target_ast, to_mutate):
            inside_time_reg.add_child(mutate_time_reg)
            mutation_number = score.all_mutants + 1
            self.notify_mutation(mutation_number, op, filename, lineno, mutant_ast)
            inside_time_reg.start('build_mutant_module')
            mutant_module = self.create_mutant_module(target_module, mutant_ast)
            inside_time_reg.stop_last()
            if mutant_module:
                inside_time_reg.start('run_tests_with_mutant')
                self.run_tests_with_mutant(test_modules, mutant_module, score)
                inside_time_reg.stop_last()
            else:
                score.inc_incompetent()
                self.notify_error()
            time_reg.add_child(inside_time_reg)
            inside_time_reg = utils.TimeRegister('mutate_ast_loop')

        return time_reg

    def create_target_ast(self, target_module):
        with open(target_module.__file__) as target_file:
            return ast.parse(target_file.read())

    def create_mutant_module(self, target_module, mutant_ast):
        try:
            mutant_code = compile(mutant_ast, 'mutant', 'exec')
            mutant_module = types.ModuleType(target_module.__name__.split('.')[-1])
            self.stdout_manager.disable_stdout()
            exec(mutant_code, mutant_module.__dict__)
            self.stdout_manager.enable_stdout()
        except Exception as exception:
            self.notify_build_module_fail(exception)
            return None

        return mutant_module

    def create_test_suite(self, tests_modules, mutant_module):
        suite = unittest.TestSuite()
        total_duration = 0
        injector = utils.ModuleInjector(mutant_module)
        for test_module, target_test, duration in tests_modules:
            injector.inject_to(test_module)
            if target_test:
                suite.addTests(unittest.TestLoader().loadTestsFromName(target_test, test_module))
            else:
                suite.addTests(unittest.TestLoader().loadTestsFromModule(test_module))
            total_duration += duration

        return suite, total_duration

    def run_tests_with_mutant(self, tests_modules, mutant_module, score):
        suite, total_duration = self.create_test_suite(tests_modules, mutant_module)
        result = utils.CustomTestResult()
        result.failfast = True
        time_reg = utils.TimeRegister() 
        runner_thread = self.run_mutation_thread(suite, total_duration, result)
        time_reg.stop()
        self.append_score_and_notify_views(score, result, runner_thread, time_reg.main_task)

    def run_mutation_thread(self, suite, total_duration, result):
        runner_thread = utils.KillableThread(target=lambda:suite.run(result))
        self.stdout_manager.disable_stdout()
        live_time = self.timeout_factor * total_duration if total_duration > 1 else 1
        runner_thread.start()
        runner_thread.join(live_time)
        self.stdout_manager.enable_stdout()
        return runner_thread

    def append_score_and_notify_views(self, score, result, runner_thread, mutant_duration):
        if runner_thread.is_alive():
            runner_thread.kill()
            self.notify_timeout()
            score.inc_timeout()
        elif result.type_error:
            self.notify_error(result.type_error[1])
            score.inc_incompetent()
        elif result.wasSuccessful():
            score.inc_survived()
            self.notify_survived(mutant_duration)
        else:
            if result.failures:
                killer = result.failures[0][0]
                exception_traceback = result.failures[0][1]
            elif result.errors:
                killer = result.errors[0][0]
                exception_traceback = result.errors[0][1]
            self.notify_killed(mutant_duration, killer, exception_traceback)
            score.inc_killed()


class Mutator:

    def __init__(self, operators):
        self.operators = operators

    def add_operator(self, operator):
        self.operators.append(operator)

    def mutate(self, target_ast, to_mutate):
        for op in self.operators:
            for mutant, lineno, time_reg in op().mutate(target_ast, to_mutate):
                yield op, lineno, mutant, time_reg

