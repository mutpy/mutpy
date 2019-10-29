import sys
from abc import abstractmethod
from collections import namedtuple

from mutpy import utils, coverage


class BaseTestSuite:
    @abstractmethod
    def add_tests(self, test_module, target_test):
        pass

    @abstractmethod
    def skip_test(self, test):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def run_with_coverage(self, coverage_injector=None):
        pass

    @abstractmethod
    def __iter__(self):
        pass


class BaseTest:

    @abstractmethod
    def __repr__(self):
        pass


class CoverageTestResult:

    def __init__(self, *args, coverage_injector=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.coverage_injector = coverage_injector
        self.always_covered_nodes = coverage_injector.covered_nodes.copy()
        self.test_covered_nodes = {}

    def start_measure_coverage(self):
        self.covered_nodes = self.coverage_injector.covered_nodes.copy()
        self.coverage_injector.covered_nodes.clear()

    def stop_measure_coverage(self, test):
        self.test_covered_nodes[repr(test)] = self.coverage_injector.covered_nodes.copy() | self.always_covered_nodes
        self.coverage_injector.covered_nodes.update(self.covered_nodes)


SerializableMutationTestResult = namedtuple(
    'SerializableMutationTestResult', [
        'is_incompetent',
        'is_survived',
        'killer',
        'exception_traceback',
        'exception',
        'tests_run',
    ]
)


class MutationTestResult:
    def __init__(self, *args, coverage_injector=None, **kwargs):
        super(MutationTestResult, self).__init__(*args, **kwargs)
        self.coverage_injector = coverage_injector
        self.passed = []
        self.failed = []
        self.type_error = None
        self.skipped = []

    def was_successful(self):
        return len(self.failed) == 0 and not self.is_incompetent()

    def is_incompetent(self):
        return bool(self.type_error)

    def is_survived(self):
        return self.was_successful()

    def _get_killer(self):
        if self.failed:
            return self.failed[0]

    def get_killer(self):
        killer = self._get_killer()
        if killer:
            return killer.name

    def get_exception_traceback(self):
        killer = self._get_killer()
        if killer:
            return killer.long_message

    def get_exception(self):
        return self.type_error

    def tests_run(self):
        return len(self.passed) + len(self.failed)

    def tests_skipped(self):
        return len(self.skipped)

    def serialize(self):
        return SerializableMutationTestResult(
            self.is_incompetent(),
            self.is_survived(),
            str(self.get_killer()),
            str(self.get_exception_traceback()),
            self.get_exception(),
            self.tests_run() - self.tests_skipped(),
        )

    def set_type_error(self, err):
        self.type_error = err

    def add_passed(self, name):
        self.passed.append(TestInfo(name))

    def add_skipped(self, name):
        self.skipped.append(TestInfo(name))

    def add_failed(self, name, short_message, long_message):
        self.failed.append(TestFailure(name, short_message, long_message))


class TestInfo:
    def __init__(self, name):
        self.name = name


class TestFailure(TestInfo):
    def __init__(self, name, short_message, long_message):
        super().__init__(name)
        self.short_message = short_message
        self.long_message = long_message


class BaseTestRunner:
    test_suite_cls = None

    def __init__(self, test_loader, timeout_factor, stdout_manager, mutate_covered):
        self.test_loader = test_loader
        self.timeout_factor = timeout_factor
        self.stdout_manager = stdout_manager
        self.mutate_covered = mutate_covered
        self.init_modules = self.find_init_modules()

    def create_empty_test_suite(self):
        return self.test_suite_cls()

    def create_test_suite(self, mutant_module):
        if not issubclass(self.test_suite_cls, BaseTestSuite):
            raise ValueError('{0} is not a subclass of {1}'.format(self.test_suite_cls, BaseTestSuite))
        suite = self.create_empty_test_suite()
        injector = utils.ModuleInjector(mutant_module)
        for test_module, target_test in self.test_loader.load():
            injector.inject_to(test_module)
            suite.add_tests(test_module, target_test)
        importer = utils.InjectImporter(mutant_module)
        importer.install()
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

    def inject_coverage(self, target_ast, target_module):
        if not self.mutate_covered:
            return None, None
        coverage_injector = coverage.CoverageInjector()
        coverage_module = coverage_injector.inject(target_ast, target_module.__name__)
        suite = self.create_test_suite(coverage_module)
        with self.stdout_manager:
            coverage_result = suite.run_with_coverage(coverage_injector=coverage_injector)
        return coverage_injector, coverage_result

    def run_test(self, test_module, target_test):
        suite = self.create_empty_test_suite()
        suite.add_tests(test_module, target_test)
        timer = utils.Timer()
        with self.stdout_manager:
            result = suite.run()
        return result, timer.stop()

    def find_init_modules(self):
        test_runner_class = utils.get_mutation_test_runner_class()
        test_runner = test_runner_class(suite=self.create_empty_test_suite())
        test_runner.start()
        test_runner.terminate()
        return list(sys.modules.keys())

    def remove_loaded_modules(self):
        for module in list(sys.modules.keys()):
            if module not in self.init_modules:
                del sys.modules[module]

    def mark_not_covered_tests_as_skip(self, mutations, coverage_result, suite):
        mutated_nodes = {mutation.node.marker for mutation in mutations}

        for test in suite:
            test_id = repr(test)
            if test_id in coverage_result.test_covered_nodes and mutated_nodes.isdisjoint(
                    coverage_result.test_covered_nodes[test_id]):
                suite.skip_test(test)
