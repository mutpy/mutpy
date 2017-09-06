import sys
import unittest

from mutpy import utils


class UnittestTestRunner:
    def __init__(self, test_loader, timeout_factor, stdout_manager, init_modules):
        self.test_loader = test_loader
        self.timeout_factor = timeout_factor
        self.stdout_manager = stdout_manager
        self.init_modules = init_modules

    def create_test_suite(self, mutant_module):
        suite = unittest.TestSuite()
        utils.InjectImporter(mutant_module).install()
        self.remove_loaded_modules()
        for test_module, target_test in self.test_loader.load():
            suite.addTests(self.get_test_suite(test_module, target_test))
        utils.InjectImporter.uninstall()
        return suite

    @utils.TimeRegister
    def run_tests_with_mutant(self, total_duration, mutant_module, mutations, coverage_result):
        suite = self.create_test_suite(mutant_module)
        if coverage_result:
            self.mark_not_covered_tests_as_skip(mutations, coverage_result, suite)
        timer = utils.Timer()
        result = self.run_mutation_test_runner(suite, total_duration)
        timer.stop()
        return result, timer.duration

    def run_mutation_test_runner(self, suite, total_duration):
        live_time = self.timeout_factor * (total_duration if total_duration > 1 else 1)
        test_runner_class = utils.get_mutation_test_runner_class()
        test_runner = test_runner_class(suite=suite)
        with self.stdout_manager:
            test_runner.start()
            result = test_runner.get_result(live_time)
            test_runner.terminate()
        return result

    def get_test_suite(self, test_module, target_test):
        if target_test:
            return unittest.TestLoader().loadTestsFromName(target_test, test_module)
        else:
            return unittest.TestLoader().loadTestsFromModule(test_module)

    def store_init_modules(self):
        test_runner_class = utils.get_mutation_test_runner_class()
        test_runner = test_runner_class(suite=unittest.TestSuite())
        test_runner.start()
        self.init_modules = list(sys.modules.keys())

    def remove_loaded_modules(self):
        for module in list(sys.modules.keys()):
            if module not in self.init_modules:
                del sys.modules[module]

    def mark_not_covered_tests_as_skip(self, mutations, coverage_result, suite):
        mutated_nodes = {mutation.node.marker for mutation in mutations}

        def iter_tests(tests):
            try:
                for test in tests:
                    iter_tests(test)
            except TypeError:
                add_skip(tests)

        def add_skip(test):
            if mutated_nodes.isdisjoint(coverage_result.test_covered_nodes[repr(test)]):
                test_method = getattr(test, test._testMethodName)
                setattr(test, test._testMethodName, unittest.skip('not covered')(test_method))

        iter_tests(suite)
