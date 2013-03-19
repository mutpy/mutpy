=====
MutPy
=====

MutPy is a mutation testing tool for Python 3.x source code.  MutPy supports
standard unittest module, generates YAML reports and has colorful output. It's
apply mutation on AST level.

Mutation testing
~~~~~~~~~~~~~~~~

From article at Wikipedia:

    **Mutation testing** (or Mutation analysis or Program mutation) evaluates
    the quality of software tests. Mutation testing involves modifying a program's
    source code or byte code in small ways. A test suite that does not detect and
    reject the mutated code is considered defective. These so-called mutations, are
    based on well-defined mutation operators that either mimic typical programming
    errors (such as using the wrong operator or variable name) or force the
    creation of valuable tests (such as driving each expression to zero). The
    purpose is to help the tester develop effective tests or locate weaknesses in
    the test data used for the program or in sections of the code that are seldom
    or never accessed during execution.

Installation
~~~~~~~~~~~~

You can easily install MutPy from PyPi:

::

    $ pip instal mutpy

... or if you want to have latest changes you can clone this repository and
install MutPy from sources:

::

    $ hg clone https://bitbucket.org/khalas/mutpy
    $ cd mutpy/
    $ python3 setup.py install

Example
~~~~~~~

Main code (``calculator.py``) - we will mutate it:

::

    def mul(x, y):
        return x * y

Test (``test_calculator.py``) - we will check its quality:

::

    from unittest import TestCase
    from calculator import mul

    class CalculatorTest(TestCase):

        def test_mul(self):
            self.assertEqual(mul(2, 2), 4)

Now we can run MutPy in the same directory where we have our sources files:

::

    $ mut.py --target calculator --unit-test test_calculator -m

This command will produce the following output:

::

    [*] Start mutation process:
       - targets: calculator
       - tests: test_calculator
    [*] All tests passed:
       - test_calculator [0.00031 s]
    [*] Start mutants generation and execution:
       - [#   1] AOR calculator.py:2  :
    --------------------------------------------------------------------------------
     1: def mul(x, y):
    ~2:     return x / y
    --------------------------------------------------------------------------------
    [0.02944 s] killed by test_mul (test_calculator.CalculatorTest)
       - [#   2] AOR calculator.py:2  :
    --------------------------------------------------------------------------------
     1: def mul(x, y):
    ~2:     return x // y
    --------------------------------------------------------------------------------
    [0.02073 s] killed by test_mul (test_calculator.CalculatorTest)
       - [#   3] AOR calculator.py:2  :
    --------------------------------------------------------------------------------
     1: def mul(x, y):
    ~2:     return x ** y
    --------------------------------------------------------------------------------
    [0.01152 s] survived
       - [#   4] SDL calculator.py:2  :
    --------------------------------------------------------------------------------
     1: def mul(x, y):
    ~2:     pass
    --------------------------------------------------------------------------------
    [0.01437 s] killed by test_mul (test_calculator.CalculatorTest)
    [*] Mutation score [0.21818 s]: 75.0%
       - all: 4
       - killed: 3 (75.0%)
       - survived: 1 (25.0%)
       - incompetent: 0 (0.0%)
       - timeout: 0 (0.0%)

First of all we run MutPy with few parameters. The most important are:

- ``--target`` - after this flag we should pass module which we want to mutate.
- ``--unit-test`` - this flag point to our unit tests module.

There are few phases in mutation process which we can see on printed by MutPy
output (marked by star ``[*]``):

- main code and tests modules loading,
- run tests with original (not mutated) code base,
- code mutation (main mutation phase),
- results summary.

There are 4 mutants generated in main mutation phase - 3 of them are killed and
only 1 mutant survived. We can see all stats at the end of MutPy output. In
this case MutPy didn't generate any incompetent (raised ``TypeError``) and
timeout (generated infinite loop) mutants. Our mutation score (killed to all
mutants ratio) is 75%.

To increase mutation score (100% is our target) we need to improve our tests.
This is a mutant which survived:

::

    def mul(x, y):
        return x ** y

This mutant survived because our test check if ``2 * 2 == 4``. Also ``2 ** 2 ==
4``, so this data aren't good to specify multiplication operation. We should
change it, eg:

::

    from unittest import TestCase
    from calculator import mul

    class CalculatorTest(TestCase):

        def test_mul(self):
            self.assertEqual(mul(2, 3), 6)

We can run MutPy again and now mutation score is equal 100%.


Command-line arguments
~~~~~~~~~~~~~~~~~~~~~~

List of all arguments with which you can run MutPy:

- ``-t TARGET [TARGET ...]``, ``--target TARGET [TARGET ...]`` - target module or package to mutate,
- ``-u UNIT_TEST [UNIT_TEST ...]``, ``--unit-test UNIT_TEST [UNIT_TEST ...]`` - test class, test method, module or package with unit tests,
- ``-m``, ``--show-mutants`` - show mutants source code,
- ``-r REPORT_FILE``, ``--report REPORT_FILE`` - generate YAML report,
- ``-f TIMEOUT_FACTOR``. ``--timeout-factor TIMEOUT_FACTOR`` - max timeout factor (default 5),
- ``-d``, ``--disable-stdout`` - try disable stdout during mutation (this option can damage your tests if you interact with ``sys.stdout``),
- ``-e``. ``--experimental-operators`` - use experimental operators,
- ``-o OPERATOR [OPERATOR ...]``, ``--operator OPERATOR [OPERATOR ...]`` - use only selected operators,
- ``--disable-operator OPERATOR [OPERATOR ...]`` - disable selected operators,
- ``-l``. ``--list-operators`` - list available operators,
- ``-p DIR``. ``--path DIR`` - extend Python path,
- ``--percentage PERCENTAGE`` - percentage of the generated mutants (mutation sampling),
- ``--coverage`` - mutate only covered code,
- ``-h``, ``--help`` - show this help message and exit,
- ``-v``, ``--version`` - show program's version number and exit,
- ``-q``, ``--quiet`` - quiet mode,
- ``--debug`` - debug mode,
- ``-c``. ``--colored-output`` - try print colored output.

Mutation operators
~~~~~~~~~~~~~~~~~~

List of MutPy mutation operators sorted by alphabetical order:

- AOR - Arithmetic Operator Replacement
- BOR - Bitwise Operator Replacement
- CDD - Classmethod Decorator Deletion
- CDI - Classmethod Decorator Insertion
- COI - Conditional Operator Insertion
- COR - Conditional Operator Replacement
- CRP - Constant Replacement
- EHD - Exception Handle Deletion
- LOR - Logical Operator Replacement
- MTR - Membership Test Replacement
- OIL - One Iteration Loop
- RIL - Reverse Iteration Loop
- SDL - Statement Deletion
- SIR - Slice Index Remove
- UOR - Unary Operator Replacement
- ZIL - Zero Iteration Loop

Experimental mutation operators:

- SDD - Staticmethod Decorator Deletion
- SDI - Staticmethod Decorator Insertion
- SWD - Self Word Deletion

License
~~~~~~~

Licensed under the Apache License, Version 2.0. See LICENSE file.
