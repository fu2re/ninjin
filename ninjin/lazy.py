import types
from functools import wraps

import public as public


def lazy(fn):
    @property
    @wraps(fn)
    def _lazyprop(self):
        attr_name = '_lazy_' + fn.__name__
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazyprop


@public.add
def listify(func):
    """`@listify` decorator"""
    @wraps(func)
    def new_func(*args, **kwargs):
        r = func(*args, **kwargs)
        if r is None:
            return []
        if isinstance(r, types.GeneratorType):
            return list(r)
        return r
    return new_func
