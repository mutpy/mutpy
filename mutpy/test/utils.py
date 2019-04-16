import os
import sys
import tempfile
import types


class MockModulesLoader:
    def __init__(self, name, source):
        self.names = [name]
        self.source = source
        self.module = types.ModuleType(name)
        self.module.__file__ = '<string>'
        self.load()

    def load(self, *args, **kwargs):
        exec(self.source, self.module.__dict__)
        sys.modules[self.names[0]] = self.module
        return [(self.module, None)]

    def get_source(self):
        return self.source


class FileMockModulesLoader:
    """Behaves like MockModulesLoader but creates the module as actual file."""

    def __init__(self, name, source):
        self.names = [name]
        self.source = source
        self.module = types.ModuleType(name)

    def __enter__(self):
        self.module_file = tempfile.NamedTemporaryFile(suffix='.py',delete=False)
        self.module_file_path = self.module_file.name
        self.module_file.write(self.source.encode())
        self.module_file.close()
        self.module.__file__ = self.module_file_path
        return self

    def load(self, *args, **kwargs):
        exec(self.source, self.module.__dict__)
        sys.modules[self.names[0]] = self.module
        return [(self.module, None)]

    def get_source(self):
        return self.source

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.module_file_path)
