import sys
import importlib
import unittest
import time
import threading
import pkgutil
import ctypes
import inspect
from _pyio import StringIO


def notmutate(sth):
    return sth

    
def timer(sth):
    return sth


class KillableThread(threading.Thread):

    def kill(self):
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(SystemExit))
            if res == 0:
                raise ValueError("Invalid thread id.")
            elif res != 1:
                raise SystemError("Thread killing failed.")


class ModulesLoaderException(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "cant't load {}".format(self.name)


class ModulesLoader:

    def __init__(self, names, path):
        self.names = names
        sys.path.insert(0, path or '.')

    def load(self):
        results = []
        for name in self.names:
            results += self.load_single(name)
        return results

    def load_single(self, name):
        if self.is_file(name):
            return self.load_file(name)
        elif self.is_package(name):
            return self.load_package(name)
        else:
            return self.load_module(name)

    def is_file(self, name):
        return name.endswith('.py')

    def is_package(self, name):
        try:
            module = importlib.import_module(name)
            return module.__file__.endswith('__init__.py')
        except ImportError:
            return False
        finally:
            sys.path_importer_cache.clear()

    def load_file(self, name):
        raise NotImplementedError('File loading is not supported!')

    def load_package(self, name):
        package = importlib.import_module(name)
        result = []
        for _, module_name, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            if not ispkg:
                module = importlib.import_module(module_name)
                result.append((module, None))
        return result

    def load_module(self, name):
        parts = name.split('.')
        to_mutate = []
        while True:
            if not parts:
                raise ModulesLoaderException(name)
            try:
                module = importlib.import_module('.'.join(parts))
                break
            except ImportError:
                to_mutate = [parts.pop()] + to_mutate

        attr = module
        for part in to_mutate:
            if hasattr(attr, part):
                attr = getattr(attr, part)
            else:
                raise ModulesLoaderException(name)

        return [(module, '.'.join(to_mutate) if to_mutate else None)]


class ModuleInjector:
    
    def __init__(self, source):
        self.source = source

    def inject_to(self, target):
        for imported_as in target.__dict__.copy():
            artefact = target.__dict__[imported_as]
            if inspect.ismodule(artefact):
                self.try_inject_module(imported_as, artefact, target)
            elif inspect.isclass(artefact) or inspect.isfunction(artefact):
                self.try_incject_class_or_function(imported_as, artefact, target)
            else:
                self.try_inject_other(imported_as, target)

    def try_inject_module(self, imported_as, module, target):
        if module.__name__ == self.source.__name__:
            self.source.__file__ = module.__file__
            target.__dict__[imported_as] = self.source

    def try_incject_class_or_function(self, imported_as, class_or_function, target):
        if class_or_function.__name__ in self.source.__dict__:
            target.__dict__[imported_as] = self.source.__dict__[class_or_function.__name__]

    def try_inject_other(self, imported_as, target):
        if imported_as in self.source.__dict__ and not self.is_restricted(imported_as):
            target.__dict__[imported_as] = self.source.__dict__[imported_as]
        
    def is_restricted(self, name):
        return name in ['__builtins__', '__name__', '__doc__', '__file__']


class StdoutManager:

    def __init__(self, disable=True):
        self.disable = disable

    def disable_stdout(self):
        if self.disable:
            sys.stdout = StringIO()

    def enable_stdout(self):
        sys.stdout = sys.__stdout__


class CustomTestResult(unittest.TestResult):

    def __init__(self, *args, **kwargs):
        self.type_error = None
        super(CustomTestResult, self).__init__(*args, **kwargs)

    def addError(self, test, err):
        if err[0] == TypeError:
            self.type_error = err
        else:
            super(CustomTestResult, self).addError(test, err)


class TimeRegister:
    timer = time.time

    def __init__(self):
        self.duration = 0
        self.start = self.timer()

    def stop(self):
        self.duration = self.timer() - self.start
        return self.duration

