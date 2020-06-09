""" Like functools.singledispatch, but dynamic, value-based dispatch. """

__all__ = ('dynamic_dispatch',)

import functools
import inspect

from typing import Union, Callable, Type, Hashable

from dynamic_dispatch._class import class_dispatch
from dynamic_dispatch._func import func_dispatch

from ._typeguard import typechecked


@typechecked(always=True)
def dynamic_dispatch(func: Union[Callable, Type, None] = None, *, default: bool = False):
    """
    Value-based dynamic-dispatch class decorator.

    Allows a class or function to have different implementations depending on the
    value of func's first parameter. The decorated class or function can act as
    the default implementation, if desired.

    Additional implementations may be registered for dispatch using the register()
    attribute of the dispatch class or function. If the implementation has a param
    of the same name as the first of func, it will be passed along.

    :Example:

        >>> @dynamic_dispatch(default=True)
        >>> def foo(bar: int):
        >>>     print(bar)
        >>>
        >>> @foo.dispatch(on=5)
        >>> def _(bar: int, baz: int):
        >>>     print(bar * baz)
        >>>
        >>> @foo.dispatch(on=10)
        >>> def _():
        >>>     print(-10)
        >>>
        >>> foo(1)
        1
        >>> foo(5, 10)
        50
        >>> foo(10)
        -10

    :Example:

        >>> @dynamic_dispatch(default=True)
        >>> class Foo:
        >>>     def __init__(self, foo: int):
        >>>         super().__init__()
        >>>         print(bar)
        >>>
        >>> @Foo.dispatch(foo=5)
        >>> class Bar(Foo):
        >>>     def __init__(self, foo, bar):
        >>>         super().__init__(foo)
        >>>         print(foo * bar)
        >>>
        >>> Foo(1)
        1
        <__main__.Foo object at ...>
        >>> Foo(5, 10)
        50
        <__main__.Bar object at ...>

    :param func: class or function to add dynamic dispatch to.
    :param default: whether or not to use func as the default implementation.
    :returns: func with dynamic dispatch
    """
    # Default was specified, wait until func is here too.
    if func is None:
        return functools.partial(dynamic_dispatch, default=default)

    # Delegate depending on wrap type.
    if inspect.isclass(func):
        return class_dispatch(func, default)

    func = func_dispatch(func, default=default)

    # Alter register to hide implicit parameter.
    dispatch = func.dispatch

    def replacement(impl: Callable = None, *, on: Hashable):
        if impl is None:
            return functools.partial(replacement, on=on)

        return dispatch(impl, arguments=inspect.signature(impl).parameters, on=on)

    # Type checker complains if we assign directly.
    setattr(func, 'dispatch', replacement)

    return func
