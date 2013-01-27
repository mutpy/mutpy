from mutpy.utils import notmutate


class Simple:
    """Simple class."""

    def __init__(self, z):
        self.z = z

    def add(self, x , y):
        return x + y

    def add_two(self, x):
        return self.add(x, 2)

    def add_etc(self, x):
        return x + ' etc.'

    def loop(self):
        i = 0

        while i != 100:
            i += 1

        return i

    def last_two(self, x):
        return x[-2:]

    def empty_string(self):
        return ''

    @notmutate
    def equivalent(self, x):
        return x[-1:-1:-1]

    def is_odd(self, x):
        if x % 2:
            return True
        return False

    @staticmethod
    def get_const():
        return 1337

    @classmethod
    def get_inc_const(cls):
        return cls.get_const() + 1

    def get_magic(self):
        return self.z

