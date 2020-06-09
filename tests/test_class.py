from abc import ABC, abstractmethod
from typing import Callable
from unittest import TestCase

from dynamic_dispatch import dynamic_dispatch


class EmptyInit:
    def __init__(self):
        pass


class OneArgInit:
    """ Comment """

    def __init__(self, abc):
        self.abc = abc
        self.abc_count = getattr(self, 'abc_count', 0) + 1


class TestClassDispatch(TestCase):
    def test_returns_class(self):
        self.assertIsInstance(dynamic_dispatch(OneArgInit), type)

    def test_wraps(self):
        wrapped = dynamic_dispatch(OneArgInit)

        self.assertEqual(OneArgInit.__doc__, wrapped.__doc__)
        self.assertEqual(OneArgInit.__name__, wrapped.__name__)
        self.assertEqual(OneArgInit.__module__, wrapped.__module__)

    def test_reject_splat_args(self):
        class Foo:
            def __init__(self, *args):
                pass

        with self.assertRaises(TypeError):
            dynamic_dispatch(Foo)

    def test_reject_kwargs(self):
        class Foo:
            def __init__(self, **kwargs):
                pass

        with self.assertRaises(TypeError):
            dynamic_dispatch(Foo)

    def test_requires_args(self):
        with self.assertRaises(TypeError):
            dynamic_dispatch(EmptyInit)
        with self.assertRaises(TypeError):
            dynamic_dispatch(EmptyInit, default=True)

    def test_abstract_class(self):
        class Foo(OneArgInit, ABC):
            @abstractmethod
            def bar(self):
                pass

        with self.assertRaises(TypeError):
            dynamic_dispatch(Foo, default=True)

        # Abstract classes are allowed if not default.
        dynamic_dispatch(Foo)

    def test_decorator(self):
        @dynamic_dispatch
        class Foo(OneArgInit):
            pass

        self.assertIsInstance(Foo, type)

    def test_decorator_with_default(self):
        @dynamic_dispatch(default=True)
        class Foo(OneArgInit):
            pass

        self.assertIsInstance(Foo, type)

    def test_has_register(self):
        wrapped = dynamic_dispatch(OneArgInit)
        self.assertTrue(hasattr(wrapped, 'dispatch'), 'wrapped class has no dispatch attribute')
        self.assertIsInstance(wrapped.dispatch, Callable)

        wrapped = dynamic_dispatch(OneArgInit, default=True)
        self.assertTrue(hasattr(wrapped, 'dispatch'), 'wrapped class has no dispatch attribute')
        self.assertIsInstance(wrapped.dispatch, Callable)

    def test_register_wraps(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo(OneArgInit):
            """ Another comment """
            pass

        reg = wrapped.dispatch(Foo, on=1)

        self.assertEqual(Foo.__doc__, reg.__doc__)
        self.assertEqual(Foo.__name__, reg.__name__)
        self.assertEqual(Foo.__module__, reg.__module__)

    def test_register_reject_splat_args(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo:
            def __init__(self, *args):
                pass

        with self.assertRaises(TypeError):
            wrapped.dispatch(Foo, on=1)

    def test_register_reject_kwargs(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo:
            def __init__(self, **kwargs):
                pass

        with self.assertRaises(TypeError):
            wrapped.dispatch(Foo, on=1)

    def test_register_non_subclass(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo:
            def __init__(self, bar):
                pass

        with self.assertRaises(TypeError):
            wrapped.dispatch(Foo, on=1)

    def test_register_fn(self):
        wrapped = dynamic_dispatch(OneArgInit)

        def foo() -> OneArgInit:
            pass

        wrapped.dispatch(foo, on=1)

    def test_register_fn_subclass(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo(OneArgInit):
            pass

        def foo() -> Foo:
            pass

        wrapped.dispatch(foo, on=1)

    def test_register_fn_non_class(self):
        wrapped = dynamic_dispatch(OneArgInit)

        def foo() -> int:
            pass

        with self.assertRaises(TypeError):
            wrapped.dispatch(foo, on=1)

    def test_register_fn_no_annotation(self):
        wrapped = dynamic_dispatch(OneArgInit)

        with self.assertRaises(TypeError):
            wrapped.dispatch(lambda: None, on=1)

    def test_register_not_hashable(self):
        wrapped = dynamic_dispatch(OneArgInit)

        with self.assertRaises(TypeError):
            wrapped.dispatch(type('foo', (OneArgInit,), {}), on=[])

    def test_register_no_value(self):
        wrapped = dynamic_dispatch(OneArgInit)

        with self.assertRaises(TypeError):
            wrapped.dispatch(type('foo', (OneArgInit,), {}))

    def test_register_duplicate_value(self):
        wrapped = dynamic_dispatch(OneArgInit)

        wrapped.dispatch(type('foo', (OneArgInit,), {}), on=1)

        with self.assertRaises(ValueError):
            wrapped.dispatch(type('bar', (OneArgInit,), {}), on=1)

    def test_register_on_fn(self):
        wrapped = dynamic_dispatch(lambda abc: abc)
        wrapped.dispatch(type('foo', (OneArgInit,), {}), on=1)

    def test_register_multiple(self):
        wrapped = dynamic_dispatch(OneArgInit)
        wrapped.dispatch(type('foo', (OneArgInit,), {}), on=1)
        wrapped.dispatch(type('bar', (OneArgInit,), {}), on=2)

    def test_register_multi_key(self):
        wrapped = dynamic_dispatch(OneArgInit)
        impl = type('foo', (OneArgInit,), {})

        wrapped.dispatch(impl, on=1)
        wrapped.dispatch(impl, on=2)

    def test_dispatch_default(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        args = (1,)
        obj = wrapped(*args)

        self.assertIsInstance(obj, OneArgInit)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, 1)

    def test_decorator_dispatch_default(self):
        @dynamic_dispatch(default=True)
        class Foo:
            def __init__(self, a):
                self.a = a
                self.a_count = getattr(self, 'a_count', 0) + 1

        obj = Foo(1)

        self.assertIsInstance(obj, Foo)
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.a_count, 1)

    def test_dispatch_default_exc(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        with self.assertRaises(TypeError):
            wrapped(1, 2)

    def test_dispatch_no_args(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc = 1

        class Foo(OneArgInit):
            def __init__(self):
                super().__init__(abc)

        wrapped.dispatch(Foo, on=abc)
        obj = wrapped(abc)

        self.assertIsInstance(obj, OneArgInit)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, abc)

    def test_decorator_dispatch(self):
        @dynamic_dispatch(default=True)
        class Foo:
            def __init__(self, a):
                self.a = a
                self.a_count = getattr(self, 'a_count', 0) + 1

        @Foo.dispatch(on=1)
        class Bar(Foo):
            def __init__(self, b):
                super().__init__(1)
                self.b = b
                self.b_count = getattr(self, 'b_count', 0) + 1

        args = (1, 2)
        obj = Foo(*args)

        self.assertIsInstance(obj, Foo)
        self.assertEqual(obj.a, args[0])
        self.assertEqual(obj.a_count, 1)
        self.assertEqual(obj.b, args[1])
        self.assertEqual(obj.b_count, 1)

    def test_dispatch_no_args_type_error(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc = 1

        class Foo(OneArgInit):
            def __init__(self):
                super().__init__(abc)

        wrapped.dispatch(Foo, on=abc)
        with self.assertRaises(TypeError):
            wrapped(abc, 2)

    # noinspection DuplicatedCode
    def test_dispatch_one_arg(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc, bar_ = 1, 2

        class Foo(OneArgInit):
            def __init__(self, bar):
                super().__init__(abc)
                self.bar = bar
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Foo, on=abc)
        obj = wrapped(abc, bar_)

        self.assertIsInstance(obj, Foo)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, abc)
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, bar_)

    # noinspection DuplicatedCode
    def test_dispatch_override_key(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc_, bar_ = 3, 4

        class Baz(OneArgInit):
            def __init__(self, abc, bar):
                super().__init__(abc)
                self.bar = bar
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=abc_)
        obj = wrapped(abc_, bar_)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, abc_)
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, bar_)

    # noinspection DuplicatedCode
    def test_dispatch_multi_arg(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        args = (1, 2, 3, 4)

        class Baz(OneArgInit):
            def __init__(self, d, e, f):
                super().__init__(args[0])
                self.bar = d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=args[0])
        obj = wrapped(*args)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, args[0])
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, args[1:])

    # noinspection DuplicatedCode
    def test_dispatch_multi_arg_override_key(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        args = (1, 2, 3, 4)

        class Baz(OneArgInit):
            def __init__(self, abc, d, e, f):
                super().__init__(abc)
                self.bar = abc, d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=args[0])
        obj = wrapped(*args)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, args[0])
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, args)

    # noinspection DuplicatedCode
    def test_dispatch_multi_arg_override_key_reorder(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        args = (1, 2, 3, 4)

        class Baz(OneArgInit):
            def __init__(self, d, e, abc, f):
                super().__init__(abc)
                self.bar = d, e, abc, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=args[0])
        obj = wrapped(*args)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, args[0])
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, (*args[1:3], args[0], *args[3:]))

    def test_dispatch_arg_type_error(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        args = (1, 2, 3)

        class Baz(OneArgInit):
            def __init__(self, d, e, f):
                super().__init__(args[0])
                self.bar = d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=args[0])

        with self.assertRaises(TypeError):
            wrapped(*args)

    # noinspection DuplicatedCode
    def test_dispatch_kwarg(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc = 1
        kwargs = dict(f=4, e=4, d=2)

        class Baz(OneArgInit):
            def __init__(self, *, d, e, f):
                super().__init__(abc)
                self.bar = d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=abc)
        obj = wrapped(abc, **kwargs)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, abc)
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, tuple(kwargs[key] for key in sorted(kwargs)))

    # noinspection DuplicatedCode
    def test_dispatch_kwarg_override_key(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc = 1
        kwargs = dict(f=4, e=4, d=2)

        class Baz(OneArgInit):
            def __init__(self, abc, *, d, e, f):
                super().__init__(abc)
                self.bar = abc, d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=abc)
        obj = wrapped(abc, **kwargs)

        self.assertIsInstance(obj, Baz)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.abc, abc)
        self.assertEqual(obj.bar_count, 1)
        self.assertEqual(obj.bar, (abc, *tuple(kwargs[key] for key in sorted(kwargs))))

    def test_dispatch_kwarg_type_error(self):
        wrapped = dynamic_dispatch(OneArgInit, default=True)

        abc = 1
        kwargs = dict(f=4, d=2)

        class Baz(OneArgInit):
            def __init__(self, *, d, e, f):
                super().__init__(abc)
                self.bar = d, e, f
                self.bar_count = getattr(self, 'bar_count', 0) + 1

        wrapped.dispatch(Baz, on=abc)

        with self.assertRaises(TypeError):
            wrapped(abc, **kwargs)

    def test_dispatch_multi(self):
        wrapped = dynamic_dispatch(OneArgInit)

        class Foo(OneArgInit):
            def __init__(self, baz):
                super().__init__(1)
                self.baz = baz
                self.baz_count = getattr(self, 'baz_count', 0) + 1

        class Bar(OneArgInit):
            def __init__(self, qux):
                super().__init__(2)
                self.qux = qux
                self.qux_count = getattr(self, 'qux_count', 0) + 1

        wrapped.dispatch(Foo, on=1)
        wrapped.dispatch(Bar, on=2)

        foo = wrapped(1, 5)

        def check_foo():
            self.assertIsInstance(foo, Foo)
            self.assertEqual(foo.abc, 1)
            self.assertEqual(foo.abc_count, 1)
            self.assertEqual(foo.baz, 5)
            self.assertEqual(foo.baz_count, 1)
            self.assertFalse(hasattr(foo, 'qux'))
        check_foo()

        bar = wrapped(2, 10)
        self.assertIsInstance(bar, Bar)
        self.assertEqual(bar.abc, 2)
        self.assertEqual(bar.abc_count, 1)
        self.assertEqual(bar.qux, 10)
        self.assertEqual(bar.qux_count, 1)
        self.assertFalse(hasattr(bar, 'baz'))

        check_foo()

    def test_can_instantiate_registered_impl(self):
        @dynamic_dispatch
        class Foo(OneArgInit):
            pass

        @Foo.dispatch(on=1)
        class Bar(Foo):
            def __init__(self, a, *, b):
                super().__init__(1)
                self.a = a
                self.b = b
                self.a_count = getattr(self, 'a_count', 0) + 1
                self.b_count = getattr(self, 'b_count', 0) + 1

        obj = Bar(2, b=3)
        self.assertIsInstance(obj, Bar)
        self.assertEqual(obj.abc, 1)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.a, 2)
        self.assertEqual(obj.a_count, 1)
        self.assertEqual(obj.b, 3)
        self.assertEqual(obj.b_count, 1)

    def test_can_instantiate_unregistered_subclass(self):
        @dynamic_dispatch
        class Foo(OneArgInit):
            pass

        class Bar(Foo):
            def __init__(self, a):
                super().__init__(1)
                self.a = a
                self.a_count = getattr(self, 'a_count', 0) + 1

        obj = Bar(5)
        self.assertIsInstance(obj, Bar)
        self.assertEqual(obj.abc, 1)
        self.assertEqual(obj.abc_count, 1)
        self.assertEqual(obj.a, 5)
        self.assertEqual(obj.a_count, 1)
