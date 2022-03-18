from abc import ABCMeta, abstractmethod
from io import TextIOWrapper
from typing import Callable, ClassVar, Deque, Dict, Type, List, TypeVar, Tuple, Optional, Iterable
from typing_extensions import Self
import click
import re
import collections


class LineRegexFilterBase(metaclass=ABCMeta):
    __slots__ = ('_pattern', '_cpattern')
    _pattern: str
    _cpattern: re.Pattern | None

    def __call__(self: Self, line: str) -> str | None:
        if self._cpattern is None:
            self._cpattern = re.compile(self._pattern)
        new_line: str
        rcount: int
        new_line, rcount = self._cpattern.subn(
            self._match_replace_callback, line)
        if rcount <= 0:
            return None
        return new_line

    @abstractmethod
    def _match_replace_callback(self: Self, match: re.Match) -> str:
        raise NotImplementedError


class LineRegexFilter(LineRegexFilterBase):
    __slots__ = ('_replacer')
    _replacer: Callable[[str], str]

    @classmethod
    def replacer(cls: Type[Self], pattern: str) -> Callable[[Callable[[str], str]], Self]:
        def decorator(replacer: Callable[[str], str]) -> Self:
            return cls(replacer, pattern)
        return decorator

    def __init__(self: Self, replacer: Callable[[str], str], pattern: str) -> None:
        self._pattern = pattern
        self._cpattern = None
        self._replacer = replacer

    def _match_replace_callback(self: Self, match: re.Match) -> str:
        matchstr: str = match.group(0)
        return self._replacer(matchstr)


class CompositeLineRegexFilter(LineRegexFilterBase, object):
    __slots__ = ('_subfilters')
    _subfilters: Dict[str, LineRegexFilter]

    def __init__(self: Self, *filters: LineRegexFilter) -> None:
        self._subfilters = {}
        subpatterns: List[str] = []

        for f in filters:
            key_name = f'_{hex(id(f)).removeprefix("0x")}'
            self._subfilters[key_name] = f
            subpatterns.append(f'(?P<{key_name}>{f._pattern})')

        self._pattern = '|'.join(subpatterns)
        self._cpattern = None

    def _match_replace_callback(self: Self, match: re.Match) -> str:
        if match.lastgroup is None or match.lastgroup not in self._subfilters:
            return match.string
        matchstr: str = match.group(0)
        return self._subfilters[match.lastgroup]._replacer(matchstr)


_T = TypeVar('_T')
_U = TypeVar('_U')


def filtermap(func: Callable[[_U], _T | None], iterable: Iterable[_U]) -> Iterable[_T]:
    for it in iterable:
        res: _T | None = func(it)
        if res is not None:
            yield res


@LineRegexFilter.replacer(
    r'(?:(?<=[^0-9])|^)' +
    # 99:99:99
    r'(?:[0-9]{2}:){2}[0-9]{2}' +
    r'(?=[^0-9]|$)'
)
def timestamp_filter(line: str) -> str:
    return click.style(line, italic=True)


class Rgb:
    Min: ClassVar[int] = 70
    Max: ClassVar[int] = 255
    Range: ClassVar[int] = Min - Max

    @classmethod
    def from_int_list(cls: Type[Self], lst: List[int]) -> Tuple[int, int, int]:
        rgb_out = [0, 0, 0]
        extra_count = len(lst) % 3
        even_count = len(lst) - extra_count
        for i in range(even_count):
            rgb_out[i % 3] = (rgb_out[i % 3] + lst[i] + hash(i)) % cls.Range
        for i in range(extra_count):
            amount: int = (
                (lst[even_count + i] + hash(even_count + i)) // 3) % cls.Range
            rgb_out[0] += amount
            rgb_out[1] += amount
            rgb_out[2] += amount
        rgb_out[0] += cls.Min
        rgb_out[1] += cls.Min
        rgb_out[2] += cls.Min
        return (rgb_out[0], rgb_out[1], rgb_out[2])


@LineRegexFilter.replacer(
    r'(?:(?<=[^0-9])|^)' +
    # 250-255|200-249|100-199|10-99|0-9. (x3)
    r'(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])\.){3}' +
    # 250-255|200-249|100-199|10-99|0-9
    r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])' +
    r'(?=[^0-9]|$)'
)
def ipv4_filter(line: str) -> str:
    ip_segments: List[int] = [int(part) for part in line.split('.')]
    return click.style(line, fg=Rgb.from_int_list(ip_segments))

@LineRegexFilter.replacer(
    r'(?:(?<=[^0-9a-fA-F])|^)' +
    r'(?:' +

    # 1111:2222:3333:4444:5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|' +
    # 1111:2222:3333:4444:5555:6666:7777::
    r'(?:[0-9a-fA-F]{1,4}:){6,6}[1-9a-fA-F][0-9a-fA-F]{0,3}::|' +
    # 1111:2222:3333:4444:5555:6666:: - 1111:2222:3333:4444:5555:6666::8888
    r'(?:[0-9a-fA-F]{1,4}:){5,5}[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3})?|' +
    # 1111:2222:3333:4444:5555:: - 1111:2222:3333:4444:5555::7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){4,4}[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,1})?|' +
    # 1111:2222:3333:4444:: - 1111:2222:3333:4444::6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){3,3}[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,2})?|' +
    # 1111:2222:3333:: - 1111:2222:3333::5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){2,2}[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,3})?|' +
    # 1111:2222:: - 1111:2222::4444:5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){1,1}[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,4})?|' +
    # 1111:: - 1111::3333:4444:5555:6666:7777:8888
    r'[1-9a-fA-F][0-9a-fA-F]{0,3}::(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,5})?|' +
    # ::2222 - ::2222:3333:4444:5555:6666:7777:8888
    r'::[1-9a-fA-F][0-9a-fA-F]{0,3}(?:[0-9a-fA-F]{0,4}){0,6}' +

    # NOTE: the ipv6 address "::" was deliberately excluded as it is exceptionally ambiguous
    r')' +
    r'(?=[^0-9a-fA-F]|$)'
)
def ipv6_filter(line: str) -> str:
    ip_sections: List[List[str]] = [section.split(
        ':') for section in line.split('::', maxsplit=1)]
    ip_segments: List[int] = [int(segment, 16) for segment in ip_sections[0]]
    if len(ip_sections) > 1:
        implied_segments = 8 - (len(ip_sections[0]) + len(ip_sections[1]))
        ip_segments.extend([0] * implied_segments)
        ip_segments.extend([int(segment, 16) for segment in ip_sections[1]])
    return click.style(line, fg=Rgb.from_int_list(ip_segments))


@click.command(context_settings={'help_option_names': ['-h', '--help']}, options_metavar="[OPTIONS...]", help="Prints the lines of FILE (or stdin if no file is specified) after applying the filters specified by OPTIONS.")
@click.option('-f', '--first', type=click.IntRange(min=0, min_open=True), metavar="NUM", help="Print the first NUM lines.")
@click.option('-l', '--last', type=click.IntRange(min=0, min_open=True), metavar="NUM", help="Print the last NUM lines.")
@click.option('-t', '--timestamps', help="Print lines that contain a timestamp in HH:MM:SS format.", is_flag=True)
@click.option('-i', '--ipv4', help="Print lines that contain an IPv4 address, matching IPs are highlighted.", is_flag=True)
@click.option('-I', '--ipv6', help="Print lines that contain an IPv6 address, matching IPs are highlighted.", is_flag=True)
@click.version_option(prog_name='util.py', package_name='pylogutil')
@click.argument('file', type=click.File('r'), metavar="[FILE]", default='-')
# TODO: we could optimize situations where the only remaining values needed are "last" by skipping line by line through the file and only caching the seek_from_end position for each line
#       we could then go line-by-line backwards using the cached seek offsets.
#       we could also procure a open source library for backwards line-by-line file access
def main(first: Optional[int], last: Optional[int], timestamps: bool, ipv4: bool, ipv6: bool, file: TextIOWrapper) -> None:
    if first is None and last is None:
        return

    line_iter: Iterable[str] = file

    base_filters: List[LineRegexFilter] = []
    if timestamps:
        base_filters.append(timestamp_filter)
    if ipv4:
        base_filters.append(ipv4_filter)
    if ipv6:
        base_filters.append(ipv6_filter)

    if base_filters:
        line_iter = filtermap(
            CompositeLineRegexFilter(*base_filters), line_iter)

    filtered_lines: List[str] = []

    if first is not None and first > 0:
        first_lines: int = 0
        for line in line_iter:
            filtered_lines.append(line)
            first_lines += 1
            if first_lines >= first:
                break

    if last is not None and last > 0:
        last_line_buff: Deque[str] = collections.deque(maxlen=last)
        for line in line_iter:
            last_line_buff.append(line)
        filtered_lines.extend(last_line_buff)

    for line in filtered_lines:
        click.echo(line.rstrip('\n'), color=True)


if __name__ == '__main__':
    main()

__all__ = ['main']
