from .unittest_runner import UnittestTestRunner


def pytest_installed():
    import importlib
    pytest_loader = importlib.find_loader('pytest')
    return pytest_loader is not None


class TestRunnerNotInstalledException(Exception):
    pass


def __pytest_not_installed(*args, **kwargs):
    raise TestRunnerNotInstalledException(
        'Pytest is not installed. Please run "pip install pytest" to resolve this issue.'
    )


if pytest_installed():
    from .pytest_runner import PytestTestRunner
else:
    PytestTestRunner = __pytest_not_installed
