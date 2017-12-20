import unittest

from mutpy.test_runners.base import CoverageTestResult, BaseTestSuite, BaseTestRunner, MutationTestResult, BaseTest


class UnittestMutationTestResult(unittest.TestResult):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_error = None
        self.failfast = True
        self.mutation_test_result = MutationTestResult()

    def addSuccess(self, test):
        super().addSuccess(test)
        self._add_success(test)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._add_success(test)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._add_latest_unexpected_success()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._add_latest_failure()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._add_latest_skip()

    def addError(self, test, err):
        if err[0] == TypeError:
            self.mutation_test_result.set_type_error(err)
        else:
            super(UnittestMutationTestResult, self).addError(test, err)
            self._add_latest_error()

    def _add_success(self, test):
        self.mutation_test_result.add_passed(str(test))

    def _add_latest_failure(self):
        failure = self.failures[-1]
        self.mutation_test_result.add_failed(str(failure[0]), self._get_short_message(failure[1]), failure[1])

    def _add_latest_error(self):
        failure = self.errors[-1]
        self.mutation_test_result.add_failed(str(failure[0]), self._get_short_message(failure[1]), failure[1])

    def _add_latest_unexpected_success(self):
        failure = self.unexpectedSuccesses[-1]
        self.mutation_test_result.add_failed(str(failure[0]), 'Unexpected success')

    def _add_latest_skip(self):
        skip = self.skipped[-1]
        self.mutation_test_result.add_skipped(str(skip))

    @staticmethod
    def _get_short_message(traceback):
        return traceback.split("\n")[-2]


class UnittestCoverageResult(CoverageTestResult, unittest.TestResult):

    def startTest(self, test):
        super().startTest(test)
        self.start_measure_coverage()

    def stopTest(self, test):
        super().stopTest(test)
        self.stop_measure_coverage(UnittestTest(test))


class UnittestTestSuite(BaseTestSuite):

    def __init__(self):
        self.suite = unittest.TestSuite()

    def add_tests(self, test_module, target_test):
        self.suite.addTests(self.load_tests(test_module, target_test))

    def skip_test(self, test):
        test_method = getattr(test.internal_test_obj, test.internal_test_obj._testMethodName)
        setattr(test.internal_test_obj, test.internal_test_obj._testMethodName,
                unittest.skip('not covered')(test_method))

    def run(self):
        result = UnittestMutationTestResult()
        self.suite.run(result)
        return result.mutation_test_result

    def run_with_coverage(self, coverage_injector=None):
        coverage_result = UnittestCoverageResult(coverage_injector=coverage_injector)
        self.suite.run(coverage_result)
        return coverage_result

    def load_tests(self, test_module, target_test):
        if target_test:
            return unittest.TestLoader().loadTestsFromName(target_test, test_module)
        else:
            return unittest.TestLoader().loadTestsFromModule(test_module)

    def iter_tests(self, tests):
        try:
            for test in tests:
                self.iter_tests(test)
        except TypeError:
            yield tests

    def __iter__(self):
        for test in self.iter_tests(self.suite):
            yield UnittestTest(test)


class UnittestTest(BaseTest):

    def __repr__(self):
        return repr(self.internal_test_obj)

    def __init__(self, internal_test_obj):
        self.internal_test_obj = internal_test_obj


class UnittestTestRunner(BaseTestRunner):
    test_suite_cls = UnittestTestSuite
