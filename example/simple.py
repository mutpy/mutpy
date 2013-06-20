from mutpy.utils import notmutate


class Base:
    X = 1

    def foo(self):
        return 1

    def bar(self):
        self.x = 1


class Simple(Base):
    """Simple class."""

    X = 2

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

    def negate_number(self, x):
        return -x

    def negate_bool(self, x):
        return not x

    def negate_bitwise(self, x):
        return ~x

    def bool_conjunction(self, a, b):
        return a or b

    def bitwise_conjunction(self, a, b):
        return a | b

    def foo(self):
        return 2

    def bar(self):
        super().bar()
        self.x += 1

    def handle_exception(self):
        try:
            raise AttributeError
        except AttributeError:
            return 1
