#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper, wraps


def disable(func):
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:
    >>> memo = disable
    we can turn off memo using only this line
    memo = disable (see below after def memo(func):...)
    """
    return func


def decorator(decorator_as_func):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """

    def wrapper(func):
        return update_wrapper(decorator_as_func(func), func)

    return update_wrapper(wrapper, decorator_as_func)


def countcalls(func):
    """Decorator that counts calls made to the function decorated."""

    @wraps(func)
    def wrapper(*args):
        res = func(*args)
        wrapper.calls += 1
        update_wrapper(wrapper, func)
        return res

    wrapper.calls = 0
    return wrapper


def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """
    memo_store = {}

    @wraps(func)
    def wrapper(*args):
        if args in memo_store:
            return memo_store[args]
        else:
            res = func(*args)
            update_wrapper(wrapper, func)
            memo_store[args] = res
            return res

    return wrapper


# we can turn off memo uncomment only this line
# memo = disable


def n_ary(func):
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.

    """

    def split_args(source_func, *args):
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            return source_func(*args)
        else:
            return split_args(source_func, args[0], split_args(source_func, *args[1:]))

    @wraps(func)
    def wrapper(*args):
        res = split_args(func, *args)
        update_wrapper(wrapper, func)
        return res

    return wrapper


def trace(filler):
    """Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    """

    def log_trace(func):
        def wrapper(*args):
            const_args = ",".join(str(x) for x in args)
            print "{} --> {}({})".format(filler * func.level, func.__name__, const_args)
            func.level += 1
            res = func(*args)
            func.level -= 1
            print "{} <-- {}({}) == {}".format(filler * func.level, func.__name__, const_args, res)
            if func.level != 0:
                return res
            else:
                return

        func.level = 0
        return update_wrapper(wrapper, func)

    return log_trace


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("____")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)  # calls 1, with memo 1
    print bar(4, 3, 2)  # calls 2, with memo 2
    print bar(4, 3, 2, 1)  # calls 3 with memo 3
    # for three bar all calls 6, with memo 3

    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
