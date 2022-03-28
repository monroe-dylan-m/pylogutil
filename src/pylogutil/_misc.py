"""Misc abstract functions"""

from typing import Callable, Iterable, ParamSpec, TypeVar

__all__ = ['filtermap', 'indirect_filter']

_T = TypeVar('_T')
_U = TypeVar('_U')
_P = ParamSpec('_P')


def filtermap(func: Callable[[_U], _T | None],
              iterable: Iterable[_U]
              ) -> Iterable[_T]:
    """Acts like a combination of `filter` and `map` in that the supplied 
    `func` is able to both replace items in `iterable` and also exclude them 
    from the generated items.

    Args:
        func: A function that takes an item from `iterable` and returns a 
            value or `None`. If the `func` returns `None`, the item it was 
            processing is excluded.
        iterable: An `Iterable` of items to process.

    Returns:
        An `Iterable` which returns the processed items which were not 
        excluded."""

    for it in iterable:
        res: _T | None = func(it)
        if res is not None:
            yield res


def indirect_filter(iter_factory: Callable[_P, Iterable[_T]],
                    *args: _P.args,
                    **kwargs: _P.kwargs
                    ) -> Iterable[_T]:
    """Produces an iterable from a supplied factory function and then iterates 
    over it. The factory is not called until iteration begins.

    This is useful when the construction of an iterable causes side-effects. 
    For example, if the constructor consumes other iterables (like a filter 
    does, hence the name `indirect_filter`).

    Args:
        iter_factory: A function that produces an iterable.

    Returns:
        An iterable which, when iteration is requested, calls `iter_factory` 
        to supply the iterator instance that is returned to the caller.

    Example:
        The following example produces an iterable that would iterate over 
        the last 5 items in **my_str_iterable**::

            >>> import collections
            >>> my_str_iterable = [f'I am string {i}!' for i in range(20)]
            >>> last_ten_str = indirect_filter(
            ...     collections.deque, my_str_iterable, max_len=5)
            >>> for string in last_ten_str:
            ...     print(string)
            I am string 16!
            I am string 17!
            I am string 18!
            I am string 19!
            I am string 20!
    """

    yield from iter_factory(*args, **kwargs)
