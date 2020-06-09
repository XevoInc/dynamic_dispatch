""" Like functools.singledispatch, but dynamic, value-based function dispatch. """

import functools
import inspect
from types import MappingProxyType
from typing import Callable, Hashable, Type

from ._typeguard import typechecked


def _lookup(key: str, typ: Type, *args, **kwargs) -> Hashable:
    """
    Gets the value of the given key in args, defaulting to the first positional.

    :param key: key to find value of in args.
    :param typ: type that dispatch is being perform on.
    :param args: positional args.
    :param kwargs: keyword args.
    :return: value of the key in the given args.
    """
    if key in kwargs:
        value = kwargs[key]
    else:
        try:
            if typ.__qualname__.endswith('.__new__'):
                value = args[1]
            else:
                value = args[0]
        except IndexError:
            raise TypeError(f'missing dispatch parameter {key!r} on {typ.__name__}')

    return value


@typechecked
def func_dispatch(func: Callable = None, *, default: bool, clazz=None):
    """
    Value-based dynamic-dispatch function decorator.

    Transforms a function into a dynamic dispatch function, which has different
    behaviors depending upon the value of its first positional parameter. The
    decorated function acts as the default implementation, if default is specified,
    and additional functions may be registered using the dispatch() attribute of
    the dispatch function.

    :param func: function to add dynamic dispatch to.
    :param default: whether or not to default when given an unregistered value.
    :param clazz: class that func is __new__ for, or None.
    :returns: dispatch function.
    """
    if func is None:
        return functools.partial(func_dispatch, default=default, clazz=clazz)

    if inspect.ismethod(func):
        raise NotImplementedError('member functions are not supported')

    if clazz is None:
        name = func.__name__
        parameters = inspect.signature(func).parameters
    else:
        name = clazz.__name__
        parameters = inspect.signature(clazz.__init__).parameters

    registry = {}

    # Find the first explicit (non-splat) positional argument. This is the dispatch parameter.
    parameters = iter(parameters.values())
    param = None
    while param is None or param.name == 'self' or param.name == 'return' or \
            param.kind == inspect.Parameter.VAR_POSITIONAL or param.kind == inspect.Parameter.VAR_KEYWORD:
        try:
            param = next(parameters)
        except StopIteration:
            raise TypeError('dispatch function does not have any explicit positional arguments') from None
    key = param.name

    @functools.wraps(func)
    def dispatch(*args, **kwargs):
        # If dispatching a class, the first argument indicates the type of class desired.
        # If that class is not the dispatch class, someone is instantiating a derived class directly.
        # In this special case, we bypass dispatch.
        if clazz is not None:
            if len(args) > 0 and inspect.isclass(args[0]):
                klass = args[0]

                if klass is not clazz and not (klass.__qualname__ == clazz.__qualname__ and clazz in klass.__bases__):
                    if issubclass(klass, clazz):
                        return func(*args, **kwargs)
                    else:
                        raise TypeError(f'cls argument for __new__ must be subclass of {clazz!r}, got {klass!r}')

        # Find dispatch param by position or key.
        value = _lookup(key, func, *args, **kwargs)

        if default:
            # Allow default to dispatch func, which we know has the dispatch param at index 0.
            impl, idx = registry.get(value, (func, 0))
        else:
            try:
                impl, idx = registry[value]
            except KeyError:
                raise ValueError(f'no registered implementations for {value!r} for {name}') from None

        if inspect.isclass(impl):
            args = args[1:]

            if idx is not None:
                idx -= 1

        if idx is None:
            # Dispatch param is not desired, remove it.
            if key in kwargs:
                del kwargs[key]
            else:
                # Not in kwargs, must be the first parameter.
                args = args[1:]
        elif idx > 0 and key not in kwargs:
            # Dispatch param is desired and it's not the first argument, so rearrange.
            args = args[1:idx + 1] + args[0:1] + args[idx + 1:]

        return impl(*args, **kwargs)

    @typechecked(always=True)
    def register(impl: Callable = None, *, arguments: MappingProxyType, on: Hashable):
        """
        Registers a new implementation for the given value of key.

        :param on: dispatch value to register this implementation on.
        :param arguments: parameters to impl.
        :param impl: implementation to associate with value.
        """
        if impl is None:
            return functools.partial(register, arguments=arguments, on=on)

        if on in registry:
            raise ValueError(f'duplicate implementation for {on!r} for {name}')

        # Determine index of dispatch parameter in this signature.
        idx = None
        for i, parameter in enumerate(arguments.values()):
            if parameter.name == key:
                if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                    # Parameter is keyword-only, so it has no 'index'.
                    idx = -1
                else:
                    idx = i

        registry[on] = impl, idx

        return impl

    dispatch.dispatch = register
    return dispatch
