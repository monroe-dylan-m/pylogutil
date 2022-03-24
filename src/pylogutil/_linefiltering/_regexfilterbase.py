"""Base classes for filtering lines using regular expressions"""

from abc import ABC, abstractmethod
from typing import Callable
from typing_extensions import Self
import functools
import re

all = ['LineRegexFilterBase', 'LineRegexFilter', 'lineregexfilter',
       'CompositeLineRegexFilter']


class LineRegexFilterBase(ABC):
    """Base class for objects that filter (and optionally replace portions of) 
    lines of text using regular expressions."""

    _pattern: str
    """A regular expression which determines what part of a line is matched."""

    _cpattern: re.Pattern | None
    """A compiled `re.Pattern` representing `_pattern`, or `None` if 
    `_pattern` has not yet been used."""

    def __call__(self: Self, line: str) -> str | None:
        """Attempts to match `_pattern` in line and passes any matches 
        to `_match_replace_callback`.

        Args:
            line: the line to match and replace against.

        Returns:
            A replacement line, or `None` if the line was not matched.
        """

        if self._cpattern is None:
            self._cpattern = re.compile(self._pattern)

        new_line: str
        rcount: int
        new_line, rcount = self._cpattern.subn(self._match_replace_callback,
                                               line)

        if rcount <= 0:
            return None

        return new_line

    @abstractmethod
    def _match_replace_callback(self: Self, match: re.Match) -> str:
        """When overridden in a derived class, implements a callback for 
        `re.sub`.

        Args:
            match: an object representing the matched text.

        Returns:
            The text the match should be replaced with. To indicate the 
            matched text should not be replaced, simply return the matched 
            text (e.g. :code:`return match.group(0)`).
        """
        raise NotImplementedError


class LineRegexFilter(LineRegexFilterBase):
    """A basic implementation of `LineRegexFilterBase` that calls a 
    supplied function to replace matched text."""

    _replacer: Callable[[str], str]
    """A function that should convert a string into its replacement."""

    def __init__(self: Self,
                 replacer: Callable[[str], str],
                 pattern: str
                 ) -> None:
        """
        Args:
            replacer: A function that should convert a string into its
                replacement.
            pattern: The regular expression to match.
        """
        self._pattern = pattern
        self._cpattern = None
        self._replacer = replacer
        functools.update_wrapper(self, replacer)

    def _match_replace_callback(self: Self, match: re.Match) -> str:
        """Invokes `_replacer` to convert the matched text to replacement
        text"""

        matchstr: str = match.group(0)
        return self._replacer(matchstr)


def lineregexfilter(pattern: str
                    ) -> Callable[[Callable[[str], str]], LineRegexFilter]:
    """Decorates a function that replaces text matched by the supplied regex
    `pattern`.

    Args:
        pattern: The regular expression pattern to match.

    Example::

        @lineregexfilter('\\bcpu\\b') # match 'cpu'
        def replacer(line: str) -> str:
            return line.upper() # convert 'cpu' to 'CPU'
    """

    def _lineregexfilter(replacer: Callable[[str], str]) -> LineRegexFilter:
        return LineRegexFilter(replacer, pattern)

    return _lineregexfilter


class CompositeLineRegexFilter(LineRegexFilterBase):
    """Represents a composite of individual `LineRegexFilter`.

    This class will match the `_pattern` all of its sub-filters and call
    each of their `LineRegexFilter._replacer` functions with matched text.

    Importantly, this composite filter will only filter a line out if 
    none of the sub-filters matched."""

    _subfilters: dict[str, LineRegexFilter]
    """The individual sub-filters, stored by id."""

    def __init__(self: Self, *filters: LineRegexFilter) -> None:
        """
        Args:
            filters: individual `LineRegexFilter` instances that should be 
                composited.

        The `_pattern` of the individual `filters` are encapsulated in 
        regex groups and combined to form this instance's `_pattern`. 
        The regex groups are given unique ids so that the sub-filter whose 
        pattern matched can be determined from the `re.Match` object.
        """

        self._subfilters = {}
        subpatterns: list[str] = []

        for f in filters:
            key_name = f'_{hex(id(f)).removeprefix("0x")}'
            self._subfilters[key_name] = f
            subpatterns.append(f'(?P<{key_name}>{f._pattern})')

        self._pattern = '|'.join(subpatterns)
        self._cpattern = None

    def _match_replace_callback(self: Self, match: re.Match) -> str:
        """Checks the group id of the pattern that was matched and delegates 
        to the appropriate `_subfilter`.`LineRegexFilter._replacer` to perform 
        the replacement of the matched text."""

        if match.lastgroup is None or match.lastgroup not in self._subfilters:
            return match.string

        matchstr: str = match.group(0)

        return self._subfilters[match.lastgroup]._replacer(matchstr)
