import unittest

from mutpy import utils
from mutpy.test.utils import FileMockModulesLoader
from mutpy.test_runners import UnittestTestRunner, PytestTestRunner

TARGET_MUL_SRC = 'def mul(x): return x * x'
TARGET_MUL_TYPEERROR_SRC = 'def mul(x): return x * "a"'


class BaseTestCases:
    """Wrapper class around abstract test superclasses to prevent unittest from running them directly."""

    class BaseTestRunnerTest(unittest.TestCase):
        TEST_RUNNER_CLS = None
        TEST_SRC_SUCCESS = None
        TEST_SRC_FAIL = None
        TEST_SRC_SKIP = None

        def setUp(self):
            if None in [self.TEST_RUNNER_CLS, self.TEST_SRC_SUCCESS, self.TEST_SRC_FAIL, self.TEST_SRC_SKIP]:
                self.fail('Subclasses must override TEST_RUNNER_CLS, TEST_SRC_SUCCESS, TEST_SRC_FAIL and TEST_SRC_SKIP')

        def run_test(self, target_src, test_src):
            with FileMockModulesLoader('target', target_src) as target_loader, \
                    FileMockModulesLoader('test', test_src) as test_loader:
                target_loader.load()
                runner = self.TEST_RUNNER_CLS(test_loader, 5, utils.StdoutManager(True), False)
                test_module, target_test = test_loader.load()[0]
                result, time = runner.run_test(test_module, target_test)
            return result

        def test_run_test_success(self):
            result = self.run_test(TARGET_MUL_SRC, self.TEST_SRC_SUCCESS)
            self.assertTrue(result.was_successful())
            self.assertFalse(result.is_incompetent())
            self.assertTrue(result.is_survived())
            self.assertIsNone(result.get_killer())
            self.assertIsNone(result.get_exception_traceback())
            self.assertIsNone(result.get_exception())
            self.assertEqual(1, result.tests_run())
            self.assertEqual(0, result.tests_skipped())
            self.assertEqual(1, len(result.passed))
            self.assertEqual(0, len(result.failed))

        def test_run_test_fail(self):
            result = self.run_test(TARGET_MUL_SRC, self.TEST_SRC_FAIL)
            self.assertFalse(result.was_successful())
            self.assertFalse(result.is_incompetent())
            self.assertFalse(result.is_survived())
            self.assertIn('test_mul', result.get_killer())
            self.assertIsNotNone(result.get_exception_traceback())
            self.assertIsNone(result.get_exception())
            self.assertEqual(1, result.tests_run())
            self.assertEqual(0, result.tests_skipped())
            self.assertEqual(0, len(result.passed))
            self.assertEqual(1, len(result.failed))

        def test_run_test_skip(self):
            result = self.run_test(TARGET_MUL_SRC, self.TEST_SRC_SKIP)
            self.assertTrue(result.was_successful())
            self.assertFalse(result.is_incompetent())
            self.assertTrue(result.is_survived())
            self.assertIsNone(result.get_killer())
            self.assertIsNone(result.get_exception_traceback())
            self.assertIsNone(result.get_exception())
            self.assertEqual(0, result.tests_run())
            self.assertEqual(1, result.tests_skipped())
            self.assertEqual(0, len(result.passed))
            self.assertEqual(0, len(result.failed))


class UnittestTestRunnerTest(BaseTestCases.BaseTestRunnerTest):
    TEST_RUNNER_CLS = UnittestTestRunner
    TEST_SRC_SUCCESS = utils.f("""
        import target
        from unittest import TestCase
        class MulTest(TestCase):
            def test_mul(self):
                self.assertEqual(target.mul(2), 4)
        """)
    TEST_SRC_FAIL = utils.f("""
        import target
        from unittest import TestCase
        class MulTest(TestCase):
            def test_mul(self):
                self.assertEqual(target.mul(2), 5)
            """)

    TEST_SRC_SKIP = (utils.f("""
        import target
        from unittest import TestCase, skip
        class MulTest(TestCase):
            @skip("test skipping")
            def test_skipped(self):
                pass
        """))


class PytestTestRunnerTest(BaseTestCases.BaseTestRunnerTest):
    TEST_RUNNER_CLS = PytestTestRunner
    TEST_SRC_SUCCESS = utils.f("""
    import target
    def test_mul():
        assert target.mul(2) == 4
    """)
    TEST_SRC_FAIL = utils.f("""
    import target
    def test_mul():
        assert target.mul(2) == 5
    """)
    TEST_SRC_SKIP = utils.f("""
    import target
    import pytest
    @pytest.mark.skip(reason="test skipping")
    def test_mul():
        assert target.mul(2) == 4
    """)
