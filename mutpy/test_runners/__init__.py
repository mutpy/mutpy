from .unittest_runner import UnittestTestRunner


def pytest_installed():
    import importlib
    pytest_loader = importlib.find_loader('pytest')
    return pytest_loader is not None


if pytest_installed():
    from .pytest_runner import PytestTestRunner
