import copy
import sys
import importlib
import unittest
import time
import pkgutil
import inspect
import types
import random
import ast
import re
from _pyio import StringIO
from collections import defaultdict, namedtuple
from multiprocessing import Process, Queue
from queue import Empty


def create_module(ast_node, module_name='mutant', module_dict=None):
    code = compile(ast_node, module_name, 'exec')
    module = types.ModuleType(module_name)
    module.__dict__.update(module_dict or {})
    exec(code, module.__dict__)
    return module


def notmutate(sth):
    return sth


class ModulesLoaderException(Exception):

    def __init__(self, name, exception):
        self.name = name
        self.exception = exception

    def __str__(self):
        return "can't load {}".format(self.name)


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
        try:
            package = importlib.import_module(name)
            result = []
            for _, module_name, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
                if not ispkg:
                    module = importlib.import_module(module_name)
                    result.append((module, None))
            return result
        except ImportError as error:
            raise ModulesLoaderException(name, error)

    def load_module(self, name):
        parts = name.split('.')
        to_mutate = []
        last_exception = None
        while True:
            if not parts:
                raise ModulesLoaderException(name, last_exception)
            try:
                module = importlib.import_module('.'.join(parts))
                break
            except ImportError as error:
                to_mutate = [parts.pop()] + to_mutate
                last_exception = error

        attr = module
        for part in to_mutate:
            if hasattr(attr, part):
                attr = getattr(attr, part)
            else:
                raise ModulesLoaderException(name, last_exception)

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


class InjectImporter:

    def __init__(self, module):
        try:
            del sys.modules[module.__name__]
        except KeyError:
            pass
        self.module = module

    def find_module(self, fullname, path=None):
        if fullname == self.module.__name__:
            return self
        else:
            return None

    def load_module(self, fullname):
        self.module.__loader__ = self
        sys.modules[fullname] = self.module

    def install(self):
        if isinstance(sys.meta_path[0], self.__class__):
            sys.meta_path[0] = self
        else:
            sys.meta_path.insert(0, self)

    @classmethod
    def uninstall(cls):
        if isinstance(sys.meta_path[0], cls):
            del sys.meta_path[0]


class StdoutManager:

    def __init__(self, disable=True):
        self.disable = disable

    def __enter__(self):
        if self.disable:
            sys.stdout = StringIO()

    def __exit__(self, type, value, traceback):
        sys.stdout = sys.__stdout__


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


class MutationTestResult(unittest.TestResult):

    def __init__(self, *args, coverage_injector=None, **kwargs):
        super(MutationTestResult, self).__init__(*args, **kwargs)
        self.type_error = None
        self.failfast = True
        self.coverage_injector = coverage_injector

    def addError(self, test, err):
        if err[0] == TypeError:
            self.type_error = err
        else:
            super(MutationTestResult, self).addError(test, err)

    def is_incompetent(self):
        return bool(self.type_error)

    def is_survived(self):
        return self.wasSuccessful()

    def get_killer(self):
        if self.failures:
            return self.failures[0][0]
        elif self.errors:
            return self.errors[0][0]

    def get_exception_traceback(self):
        if self.failures:
            return self.failures[0][1]
        elif self.errors:
            return self.errors[0][1]

    def get_exception(self):
        if self.type_error:
            return self.type_error[1]

    def serialize(self):
        return SerializableMutationTestResult(
            self.is_incompetent(),
            self.is_survived(),
            str(self.get_killer()),
            str(self.get_exception_traceback()),
            self.get_exception(),
            self.testsRun - len(self.skipped),
        )


class Timer:
    time_provider = time.time

    def __init__(self):
        self.duration = 0
        self.start = self.time_provider()

    def stop(self):
        self.duration = self.time_provider() - self.start
        return self.duration


class TimeRegister:
    executions = defaultdict(float)
    timer_class = Timer
    stack = []

    def __init__(self, method):
        self.method = method

    def __get__(self, obj, ownerClass=None):
        return types.MethodType(self, obj)

    def __call__(self, *args, **kwargs):
        if self.stack and self.stack[-1] == self.method:
            return self.method(*args, **kwargs)

        self.stack.append(self.method)
        time_reg = self.timer_class()
        result = self.method(*args, **kwargs)

        self.executions[self.method.__name__] += time_reg.stop()
        self.stack.pop()
        return result

    @classmethod
    def clean(cls):
        cls.executions.clear()
        cls.stack = []


class RandomSampler:

    def __init__(self, percentage):
        self.percentage = percentage if 0 < percentage < 100 else 100

    def is_mutation_time(self):
        return random.randrange(100) < self.percentage


class MutationSubprocess(Process):

    def __init__(self, suite):
        super().__init__()
        self.suite = suite
        self.queue = Queue()

    def run(self):
        result = MutationTestResult()
        self.suite.run(result)
        self.queue.put_nowait(result.serialize())

    def get_result(self, live_time):
        try:
            return self.queue.get(timeout=live_time)
        except Empty:
            return None


class ParentNodeTransformer(ast.NodeTransformer):

    def visit(self, node):
        if getattr(node, 'parent', None):
            node = copy.copy(node)
        node.parent = getattr(self, 'parent', None)
        node.children = []
        self.parent = node
        result_node = super().visit(node)
        self.parent = node.parent
        if self.parent:
            self.parent.children += [node] + node.children
        return result_node


def create_ast(code):
    return ParentNodeTransformer().visit(ast.parse(code))


def is_docstring(node):
    def_node = node.parent.parent
    return (isinstance(def_node, (ast.FunctionDef, ast.ClassDef, ast.Module)) and def_node.body and
            isinstance(def_node.body[0], ast.Expr) and isinstance(def_node.body[0].value, ast.Str) and
            def_node.body[0].value == node)


def get_by_python_version(classes, python_version=sys.version_info):
    result = None
    for cls in classes:
        if cls.__python_version__ <= python_version:
            if not result or cls.__python_version__ > result.__python_version__:
                result = cls
    if not result:
        raise NotImplementedError('MutPy does not support Python {}.'.format(sys.version))
    return result


def sort_operators(operators):
    return sorted(operators, key=lambda cls: cls.name())


def f(text):
    lines = text.split('\n')[1:-1]
    indention = re.search('(\s*).*', lines[0]).group(1)
    return '\n'.join(line[len(indention):] for line in lines)
