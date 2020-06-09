""" Proxy for typeguard, in case it's not installed. """

__all__ = ('typechecked',)

import functools

try:
    from typeguard import typechecked
except ModuleNotFoundError:
    def typechecked(func=None, **kwargs):
        if func is None:
            return functools.partial(typechecked, **kwargs)
        return func
