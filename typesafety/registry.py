from autoregistry import Registry


class Foo(Registry):
    pass


def test_keys_must_be_strings():
    _ = Foo[None]  # E: Argument of type "None" cannot be assigned to parameter "key" of type "str" in function "__getitem__"
