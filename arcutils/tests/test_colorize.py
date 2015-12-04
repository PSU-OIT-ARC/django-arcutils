from doctest import DocTestSuite

from arcutils import colorize


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(colorize))
    return tests
