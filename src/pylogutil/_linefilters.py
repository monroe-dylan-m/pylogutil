"""Implements various line filters that match against strings and add 
highlighting"""

from ._linefiltering._regexfilterbase import lineregexfilter
from ._linefiltering._colorgen import RgbConverter
from typing import Sequence
import click

__all__ = ['timestamp_filter', 'ipv4_filter', 'ipv6_filter']


@lineregexfilter(
    r'(?:(?<=[^0-9])|^)' +
    # 99:99:99
    r'(?:[0-9]{2}:){2}[0-9]{2}' +
    r'(?=[^0-9]|$)'
)
def timestamp_filter(line: str) -> str:
    """A filter that matches timestamps (e.g. `12:43:00`) and applies 
    styling to them."""
    return click.style(line, bold=True, fg='bright_white')


@lineregexfilter(
    r'(?:(?<=[^0-9])|^)' +
    # 250-255|200-249|100-199|10-99|0-9. (x3)
    r'(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])\.){3}' +
    # 250-255|200-249|100-199|10-99|0-9
    r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])' +
    r'(?=[^0-9]|$)'
)
def ipv4_filter(line: str) -> str:
    """A filter that matches ipv4 addresses (e.g. `172.16.32.128`) and applies 
    styling to them.

    The color that is applied is a function of the address, such that matching 
    addresses will have matching colors."""

    ip_segments: Sequence[int] = [int(part)
                                  for part in line.split('.')]

    return click.style(line, underline=True,
                       fg=RgbConverter.from_int_list_8bit(ip_segments))


@lineregexfilter(
    r'(?:(?<=[^0-9a-fA-F])|^)' +
    r'(?:' +

    # 1111:2222:3333:4444:5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|' +

    # 1111:2222:3333:4444:5555:6666:7777::
    r'(?:[0-9a-fA-F]{1,4}:){6,6}[1-9a-fA-F][0-9a-fA-F]{0,3}::|' +

    # 1111:2222:3333:4444:5555:6666:: - 1111:2222:3333:4444:5555:6666::8888
    r'(?:[0-9a-fA-F]{1,4}:){5,5}[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?::[1-9a-fA-F][0-9a-fA-F]{0,3})?|' +

    # 1111:2222:3333:4444:5555:: - 1111:2222:3333:4444:5555::7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){4,4}[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,1})?|' +

    # 1111:2222:3333:4444:: - 1111:2222:3333:4444::6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){3,3}[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,2})?|' +

    # 1111:2222:3333:: - 1111:2222:3333::5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){2,2}[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,3})?|' +

    # 1111:2222:: - 1111:2222::4444:5555:6666:7777:8888
    r'(?:[0-9a-fA-F]{1,4}:){1,1}[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,4})?|' +

    # 1111:: - 1111::3333:4444:5555:6666:7777:8888
    r'[1-9a-fA-F][0-9a-fA-F]{0,3}::' +
    r'(?:[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,5})?|' +

    # ::2222 - ::2222:3333:4444:5555:6666:7777:8888
    r'::[1-9a-fA-F][0-9a-fA-F]{0,3}(?::[0-9a-fA-F]{0,4}){0,6}' +

    # NOTE: the ipv6 address "::" was deliberately excluded as it is
    # exceptionally ambiguous
    r')' +
    r'(?=[^0-9a-fA-F]|$)'
)
def ipv6_filter(line: str) -> str:
    """A filter that matches ipv6 addresses (e.g. `2860:1FF::3:4`) and applies 
    styling to them.

    The color that is applied is a function of the address, such that matching 
    addresses will have matching colors."""

    ip_sections: Sequence[Sequence[str]] = [
        section.split(':')
        for section in line.split('::', maxsplit=1)
    ]

    ip_segments: Sequence[int] = [
        (int(segment, 16) if segment else 0)
        for segment in ip_sections[0]
    ]

    # if the ip contained '::'
    if len(ip_sections) > 1:

        # calculate how many `0` sections are implied by '::'
        implied_segments = 8 - (len(ip_sections[0]) + len(ip_sections[1]))

        ip_segments.extend([0] * implied_segments)

        ip_segments.extend(
            (int(segment, 16) if segment else 0)
            for segment in ip_sections[1])

    return click.style(line, underline=True,
                       fg=RgbConverter.from_int_list_8bit(ip_segments))
