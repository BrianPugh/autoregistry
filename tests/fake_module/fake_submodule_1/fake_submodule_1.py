import itertools  # itertools is builtin and won't have a __file__ attribute.

from .. import fake_module_1  # test imports outside of submodule


def foo():
    return fake_module_1
