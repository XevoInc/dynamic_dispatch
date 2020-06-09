""" Like functools.singledispatch, but dynamic, value-based dispatch of classes. """

import functools
import inspect
from typing import Hashable, Type, TypeVar, Callable, Union

from ._typeguard import typechecked

from ._func import func_dispatch

T_co = TypeVar('T_co', covariant=True)


@typechecked
def class_dispatch(typ: Type[T_co], default: Hashable):
    """
    Value-based dynamic-dispatch class decorator.

    Transforms a class into a dynamic dispatch class, which has different
    behaviors depending upon the value of its first positional parameter.
    The decorated class acts as the default implementation, if default is
    specified, and additional classes may be registered using the dispatch()
    static function of the dispatch class.

    :param typ: class to add dynamic dispatch to.
    :param default: whether or not to default when given an unregistered value.
    :returns: dispatch class.
    """
    if inspect.isabstract(typ) and default:
        raise TypeError('abstract classes cannot be used as a default implementation')

    # Dispatcher must also be class in case anyone wants to use isinstance with it, etc.
    @functools.wraps(typ, updated=())
    class Dispatcher(typ):
        # Dynamic dispatch on a class is equivalent to dynamic dispatch on __new__.
        # Note: the parameters for dispatch here are those of __init__ instead.
        @func_dispatch(default=default, clazz=typ)
        def __new__(cls, *args, **kwargs):
            return super().__new__(cls)

        @classmethod
        @typechecked(always=True)
        def dispatch(cls, wrap: Union[Type[T_co], Callable[..., T_co]] = None, *, on: Hashable):
            if wrap is None:
                return functools.partial(cls.dispatch, on=on)

            if not inspect.isclass(wrap):
                ret = inspect.signature(wrap).return_annotation
                if ret == inspect.Parameter.empty:
                    raise TypeError(f'function {wrap.__name__} must have annotated return type') from None

                if ret is not None and issubclass(ret, typ):
                    # It's a function that returns a subtype of the dispatch class, let's allow this.
                    cls.__new__.dispatch(wrap, arguments=inspect.signature(wrap).parameters, on=on)
                    return wrap
                else:
                    raise TypeError(f'{wrap.__name__} may not be registered for dispatch on {typ.__name__}'
                                    f'as its return type {ret!r} does not subclass the dispatch type.')
            elif not issubclass(wrap, typ):
                raise TypeError(f'only subclasses of {typ.__name__} can be registered for dynamic dispatch')
            else:
                @functools.wraps(wrap, updated=())
                class Registered(wrap):
                    __dispatch_init = True

                    def __init__(self, *args, **kwargs):
                        # Certain scenarios can cause __init__ to be called twice. This prevents it.
                        if not self.__dispatch_init:
                            return

                        self.__dispatch_init = False
                        super().__init__(*args, **kwargs)

                cls.__new__.dispatch(Registered, arguments=inspect.signature(wrap.__init__).parameters, on=on)

                return Registered

    return Dispatcher
