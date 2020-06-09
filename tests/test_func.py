from typing import Callable
from unittest import TestCase
from unittest.mock import create_autospec

from dynamic_dispatch import dynamic_dispatch


class TestFuncDispatch(TestCase):
    def test_returns_func(self):
        self.assertIsInstance(dynamic_dispatch(lambda _: _), Callable)
        self.assertIsInstance(dynamic_dispatch(lambda _: _, default=True), Callable)

    def test_wraps(self):
        def foo(_):
            """ Comment """
            pass

        wrapped = dynamic_dispatch(foo)

        self.assertEqual(foo.__doc__, wrapped.__doc__)
        self.assertEqual(foo.__name__, wrapped.__name__)
        self.assertEqual(foo.__module__, wrapped.__module__)

    def test_requires_args(self):
        with self.assertRaises(TypeError):
            dynamic_dispatch(lambda: None)
        with self.assertRaises(TypeError):
            dynamic_dispatch(lambda: None, default=True)

    def test_decorator(self):
        @dynamic_dispatch
        def _(_):
            pass

        self.assertIsInstance(_, Callable)

    def test_decorator_with_default(self):
        @dynamic_dispatch(default=True)
        def _(_):
            pass

        self.assertIsInstance(_, Callable)

    def test_has_register(self):
        wrapped = dynamic_dispatch(lambda _: _)
        self.assertTrue(hasattr(wrapped, 'dispatch'), 'wrapped function has no dispatch attribute')
        self.assertIsInstance(wrapped.dispatch, Callable)

        wrapped = dynamic_dispatch(lambda _: _, default=True)
        self.assertTrue(hasattr(wrapped, 'dispatch'), 'wrapped function has no dispatch attribute')
        self.assertIsInstance(wrapped.dispatch, Callable)

    def test_register(self):
        wrapped = dynamic_dispatch(lambda _: _)
        wrapped.dispatch(lambda _: _, on=1)

    def test_register_wraps(self):
        wrapped = dynamic_dispatch(lambda _: _)

        def foo():
            """ Doc comment """
            pass

        reg = wrapped.dispatch(foo, on=1)

        self.assertEqual(foo.__doc__, reg.__doc__)
        self.assertEqual(foo.__name__, reg.__name__)
        self.assertEqual(foo.__module__, reg.__module__)

    def test_register_not_hashable(self):
        wrapped = dynamic_dispatch(lambda _: _)
        with self.assertRaises(TypeError):
            wrapped.dispatch(lambda _: _, on=[])

    def test_register_no_value(self):
        wrapped = dynamic_dispatch(lambda _: _)

        with self.assertRaises(TypeError):
            wrapped.dispatch(lambda _: _)

    def test_register_duplicate_value(self):
        wrapped = dynamic_dispatch(lambda _: _)
        wrapped.dispatch(lambda _: _, on=1)

        with self.assertRaises(ValueError):
            wrapped.dispatch(lambda _: _, on=1)

    def test_register_multiple(self):
        wrapped = dynamic_dispatch(lambda _: _)
        wrapped.dispatch(lambda _: _, on=1)
        wrapped.dispatch(lambda _: _, on=2)

    def test_register_multi_key(self):
        wrapped = dynamic_dispatch(lambda _: _)

        def impl(_):
            return _

        wrapped.dispatch(impl, on=1)
        wrapped.dispatch(impl, on=2)

    def test_dispatch_default(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default, default=True)

        args = (1,)
        wrapped(*args)

        default.assert_called_once_with(*args)

    def test_dispatch_decorator_default(self):
        default = create_autospec(lambda _: _)

        @dynamic_dispatch(default=True)
        def foo(_):
            default(_)

        args = (1,)
        foo(*args)

        default.assert_called_once_with(*args)

    def test_dispatch_default_exc(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        with self.assertRaises(ValueError):
            wrapped(1)

        default.assert_not_called()

    def test_dispatch_no_args(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda: None)
        wrapped.dispatch(impl, on=1)

        wrapped(1)

        default.assert_not_called()
        impl.assert_called_once_with()

    def test_dispatch_no_args_type_error(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda: None)
        wrapped.dispatch(default, on=1)

        with self.assertRaises(TypeError):
            wrapped(1, 2)

        default.assert_not_called()
        impl.assert_not_called()

    def test_dispatch_one_arg(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda a: a)
        wrapped.dispatch(impl, on=1)

        args = (1, 2)
        wrapped(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args[1:])

    def test_dispatch_decorator(self):
        default = create_autospec(lambda _: _)

        @dynamic_dispatch
        def foo(_):
            default(_)

        impl = create_autospec(lambda a: a)

        @foo.dispatch(on=1)
        def bar(a):
            impl(a)

        args = (1, 2)
        foo(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args[1:])

    def test_dispatch_override_key(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda _: _)
        wrapped.dispatch(impl, on=1)

        args = (1,)
        wrapped(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args)

    def test_dispatch_multi_arg(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda a, b, c: None)
        wrapped.dispatch(impl, on=1)

        args = (1, 2, 3, 4)
        wrapped(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args[1:])

    def test_dispatch_multi_arg_override_key(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda _, a, b, c: None)
        wrapped.dispatch(impl, on=1)

        args = (1, 2, 3, 4)
        wrapped(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args)

    # noinspection DuplicatedCode
    def test_dispatch_multi_arg_override_key_reorder(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda a, b, _, c: None)
        wrapped.dispatch(impl, on=1)

        args = (1, 2, 3, 4)
        wrapped(*args)

        default.assert_not_called()
        impl.assert_called_once_with(*args[1:3], args[0], *args[3:])

    def test_dispatch_arg_type_error(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda a, b, c: None)
        wrapped.dispatch(impl, on=1)

        args = (1, 2, 3)
        with self.assertRaises(TypeError):
            wrapped(*args)

        default.assert_not_called()
        impl.assert_not_called()

    def test_dispatch_kwarg(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        def impl(*, a, b, c):
            return a, b, c

        impl = create_autospec(impl)
        wrapped.dispatch(impl, on=1)

        args = (1,)
        kwargs = dict(c=4, b=3, a=2)
        wrapped(*args, **kwargs)

        default.assert_not_called()
        impl.assert_called_once_with(**kwargs)

    def test_dispatch_kwargs_type_error(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        def impl(*, a, b, c):
            return a, b, c

        impl = create_autospec(impl)
        wrapped.dispatch(impl, on=1)

        args = (1,)
        kwargs = dict(a=2, b=3)
        with self.assertRaises(TypeError):
            wrapped(*args, **kwargs)

        default.assert_not_called()
        impl.assert_not_called()

    def test_dispatch_kwarg_override_key(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        def impl(_, *, a, b, c):
            return _, a, b, c

        impl = create_autospec(impl)
        wrapped.dispatch(impl, on=1)

        args = (1,)
        kwargs = dict(c=4, b=3, a=2)
        wrapped(*args, **kwargs)

        default.assert_not_called()
        impl.assert_called_once_with(*args, **kwargs)

    def test_dispatch_multi(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        a = create_autospec(lambda z: z)
        b = create_autospec(lambda z: z)

        wrapped.dispatch(a, on=1)
        wrapped.dispatch(b, on=2)

        a.assert_not_called()
        b.assert_not_called()

        wrapped(1, -1)
        a.assert_called_once_with(-1)
        b.assert_not_called()

        wrapped(2, -2)
        default.assert_not_called()
        a.assert_called_once()
        b.assert_called_once_with(-2)

    def test_dispatch_multi_key(self):
        default = create_autospec(lambda _: _)
        wrapped = dynamic_dispatch(default)

        impl = create_autospec(lambda _, a: _)

        wrapped.dispatch(impl, on=1)
        wrapped.dispatch(impl, on=2)

        args = (1, 2)
        wrapped(*args)

        impl.assert_called_once_with(*args)

        args = (2, 3)
        wrapped(*args)

        default.assert_not_called()
        self.assertEqual(impl.call_count, 2)
        impl.assert_called_with(*args)

    def test_fails_on_members(self):
        with self.assertRaises(TypeError):
            class Foo:
                @dynamic_dispatch
                def member(self):
                    pass
