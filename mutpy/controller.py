from os import path
import sys
import ast
import unittest
from mutpy import views, utils, coverage


class TestsFailAtOriginal(Exception):

    def __init__(self, result=None):
        self.result = result


class MutationScore:

    def __init__(self):
        self.killed_mutants = 0
        self.timeout_mutants = 0
        self.incompetent_mutants = 0
        self.survived_mutants = 0
        self.covered_nodes = 0
        self.all_nodes = 0

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

    def update_coverage(self, covered_nodes, all_nodes):
        self.covered_nodes += covered_nodes
        self.all_nodes += all_nodes

    @property
    def all_mutants(self):
        return self.killed_mutants + self.timeout_mutants + self.incompetent_mutants + self.survived_mutants


class MutationController(views.ViewNotifier):

    def __init__(self, target_loader, test_loader, views, mutant_generator,
                    timeout_factor=5, disable_stdout=False, mutate_covered=False):
        super().__init__(views)
        self.target_loader = target_loader
        self.test_loader = test_loader
        self.mutant_generator = mutant_generator
        self.timeout_factor = timeout_factor
        self.stdout_manager = utils.StdoutManager(disable_stdout)
        self.mutate_covered = mutate_covered

    def run(self):
        self.notify_initialize(self.target_loader.names, self.test_loader.names)
        try:
            timer = utils.Timer()
            self.run_mutation_process()
            self.notify_end(self.score, timer.stop())
        except TestsFailAtOriginal as error:
            self.notify_original_tests_fail(error.result)
            sys.exit(-1)
        except utils.ModulesLoaderException as error:
            self.notify_cant_load(error.name, error.exception)
            sys.exit(-2)

    def run_mutation_process(self):
        try:
            test_modules = self.load_and_check_tests()

            self.notify_passed(test_modules)
            self.notify_start()

            self.score = MutationScore()

            for target_module, to_mutate in self.target_loader.load():
                self.mutate_module(target_module, to_mutate, test_modules)
        except KeyboardInterrupt:
            pass

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
        suite = self.get_test_suite(test_module, target_test)
        result = unittest.TestResult()
        timer = utils.Timer()
        with self.stdout_manager:
            suite.run(result)
        return result, timer.stop()

    def get_test_suite(self, test_module, target_test):
        if target_test:
            return unittest.TestLoader().loadTestsFromName(target_test, test_module)
        else:
            return unittest.TestLoader().loadTestsFromModule(test_module)

    @utils.TimeRegister
    def mutate_module(self, target_module, to_mutate, test_modules):
        target_ast = self.create_target_ast(target_module)
        filename = self.get_module_base_filename(target_module)
        coverage_injector = self.inject_coverage(target_ast, target_module, test_modules)

        if coverage_injector:
            self.score.update_coverage(*coverage_injector.get_result())

        for op, lineno, mutant_ast in self.mutant_generator.mutate(target_ast, to_mutate, coverage_injector):

            mutation_number = self.score.all_mutants + 1
            self.notify_mutation(mutation_number, op, filename, lineno, mutant_ast)
            mutant_module = self.create_mutant_module(target_module, mutant_ast)
            if mutant_module:
                self.run_tests_with_mutant(test_modules, mutant_module)
            else:
                self.score.inc_incompetent()

    def inject_coverage(self, target_ast, target_module, test_modules):
        if not self.mutate_covered:
            return None
        coverage_injector = coverage.CoverageInjector()
        coverage_module = coverage_injector.inject(target_ast, target_module.__name__)
        suite, total_duration = self.create_test_suite(test_modules, coverage_module)
        result = unittest.TestResult()
        with self.stdout_manager:
            suite.run(result)
        return coverage_injector

    def get_module_base_filename(self, module):
        return path.basename(module.__file__)

    @utils.TimeRegister
    def create_target_ast(self, target_module):
        with open(target_module.__file__) as target_file:
            return utils.create_ast(target_file.read())

    @utils.TimeRegister
    def create_mutant_module(self, target_module, mutant_ast):
        try:
            with self.stdout_manager:
                return utils.create_module(
                    ast_node=mutant_ast,
                    module_name=target_module.__name__
                )
        except BaseException as exception:
            self.notify_incompetent(exception)
            return None

    def create_test_suite(self, tests_modules, mutant_module):
        suite = unittest.TestSuite()
        total_duration = 0
        injector = utils.ModuleInjector(mutant_module)
        for test_module, target_test, duration in tests_modules:
            injector.inject_to(test_module)
            suite.addTests(self.get_test_suite(test_module, target_test))
            total_duration += duration

        return suite, total_duration

    @utils.TimeRegister
    def run_tests_with_mutant(self, tests_modules, mutant_module):
        suite, total_duration = self.create_test_suite(tests_modules, mutant_module)
        result = utils.MutationTestResult()
        timer = utils.Timer()
        result = self.run_mutation_subprocess(suite, total_duration, result)
        timer.stop()
        self.update_score_and_notify_views(result, timer.duration)

    def run_mutation_subprocess(self, suite, total_duration, result):
        live_time = self.timeout_factor * (total_duration if total_duration > 1 else 1)
        process = utils.MutationSubprocess(suite=suite)
        with self.stdout_manager:
            process.start()
            result = process.get_result(live_time)
            process.terminate()
        return result

    def update_score_and_notify_views(self, result, mutant_duration):
        if not result:
            self.update_timeout_mutant()
        elif result['is_incompetent']:
            exception = result['exception']
            self.update_incompetent_mutant(exception)
        elif result['is_survieved']:
            self.update_survived_mutant(mutant_duration)
        else:
            self.update_killed_mutant(mutant_duration, result['killer'], result['exception_traceback'])

    def update_timeout_mutant(self):
        self.notify_timeout()
        self.score.inc_timeout()

    def update_incompetent_mutant(self, exception):
        self.notify_incompetent(exception)
        self.score.inc_incompetent()

    def update_survived_mutant(self, duration):
        self.notify_survived(duration)
        self.score.inc_survived()

    def update_killed_mutant(self, duration, killer, exception_traceback):
        self.notify_killed(duration, killer, exception_traceback)
        self.score.inc_killed()


class Mutator:

    def __init__(self, operators, percentage):
        self.operators = operators
        self.sampler = utils.RandomSampler(percentage)

    def add_operator(self, operator):
        self.operators.append(operator)

    def mutate(self, target_ast, to_mutate, coverage_injector):
        for op in utils.sort_operators(self.operators):
            for mutant, lineno in op().mutate(target_ast, to_mutate, self.sampler, coverage_injector):
                yield op, lineno, mutant

