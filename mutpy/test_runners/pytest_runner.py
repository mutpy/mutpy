import pytest
from _pytest.config import default_plugins

from mutpy.test_runners.base import BaseTestSuite, BaseTestRunner, MutationTestResult, CoverageTestResult, BaseTest


class PytestMutpyPlugin:

    def __init__(self, skipped_tests):
        self.skipped_tests = skipped_tests
        self.mutation_test_result = MutationTestResult()

    def has_failed_before(self, nodeid):
        return next((test for test in self.mutation_test_result.failed if test.name == nodeid), None) is not None

    def has_been_skipped_before(self, nodeid):
        return next((test for test in self.mutation_test_result.skipped if test.name == nodeid), None) is not None

    def pytest_collection_modifyitems(self, items):
        for item in items:
            if item.nodeid in self.skipped_tests:
                item.add_marker(pytest.mark.skip)

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.mutation_test_result.add_skipped(report.nodeid)
        elif report.failed and not self.has_failed_before(report.nodeid):
            if 'TypeError' in report.longrepr.reprcrash.message:
                self.mutation_test_result.set_type_error(TypeError(str(report.longrepr.reprcrash)))
            else:
                if not hasattr(report, 'longreprtext'):
                    with open("Output.txt", "w") as text_file:
                        text_file.write(report.nodeid + ' ' + vars(report))
                self.mutation_test_result.add_failed(report.nodeid, report.longrepr.reprcrash.message.splitlines()[0],
                                                     report.longreprtext)
        elif report.passed and report.when == 'teardown' and not self.has_failed_before(report.nodeid) \
                and not self.has_been_skipped_before(report.nodeid):
            self.mutation_test_result.add_passed(report.nodeid)


class PytestMutpyCoveragePlugin:

    def __init__(self, coverage_injector):
        self.current_test = None
        self.coverage_result = CoverageTestResult(coverage_injector=coverage_injector)

    def pytest_runtest_setup(self, item):
        self.coverage_result.start_measure_coverage()
        self.current_test = item

    def pytest_runtest_teardown(self, nextitem):
        self.coverage_result.stop_measure_coverage(PytestTest(self.current_test))
        self.current_test = None


class PytestMutpyTestDiscoveryPlugin:
    def __init__(self):
        self.tests = []

    def pytest_collection_modifyitems(self, items):
        for item in items:
            self.tests.append(item)


class PytestTestSuite(BaseTestSuite):
    def __init__(self):
        self.tests = set()
        self.skipped_tests = set()

    def add_tests(self, test_module, target_test):
        if target_test:
            self.tests.add('{0}::{1}'.format(test_module.__file__, target_test))
        elif hasattr(test_module, '__file__'):
            self.tests.add(test_module.__file__)
        else:
            self.tests.add(test_module.__name__)

    def skip_test(self, test):
        self.skipped_tests.add(test.internal_test_obj.nodeid)

    def run(self):
        mutpy_plugin = PytestMutpyPlugin(skipped_tests=self.skipped_tests)
        pytest.main(args=list(self.tests) + ['-x', '-p', 'no:terminal'], plugins=list(default_plugins) + [mutpy_plugin])
        return mutpy_plugin.mutation_test_result

    def run_with_coverage(self, coverage_injector=None):
        mutpy_plugin = PytestMutpyCoveragePlugin(coverage_injector=coverage_injector)
        pytest.main(list(self.tests) + ['-p', 'no:terminal'], plugins=list(default_plugins) + [mutpy_plugin])
        return mutpy_plugin.coverage_result

    def __iter__(self):
        mutpy_plugin = PytestMutpyTestDiscoveryPlugin()
        pytest.main(args=list(self.tests) + ['--collect-only', '-p', 'no:terminal'],
                    plugins=list(default_plugins) + [mutpy_plugin])
        for test in mutpy_plugin.tests:
            yield PytestTest(test)


class PytestTest(BaseTest):

    def __repr__(self):
        return self.internal_test_obj.nodeid

    def __init__(self, internal_test_obj):
        self.internal_test_obj = internal_test_obj


class PytestTestRunner(BaseTestRunner):
    test_suite_cls = PytestTestSuite
