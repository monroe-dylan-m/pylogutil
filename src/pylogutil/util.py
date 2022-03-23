"""Implements a console interface for interacting with logs."""

from ._linefiltering._regexfilterbase import (LineRegexFilter,
                                              CompositeLineRegexFilter)
from ._linefilters import ipv4_filter, ipv6_filter, timestamp_filter
from ._misc import indirect_filter, filtermap
from typing import Iterable, Optional, TextIO
import click
import collections
import itertools

__all__ = ['clilogfilter', 'main']


@click.command(
    context_settings={'help_option_names': ['-h', '--help']},
    options_metavar="[OPTIONS...]",
    no_args_is_help=True,
    help="Prints the lines of FILE (or stdin if no file is specified) " +
    "after applying the filters specified by OPTIONS.")
@click.option('-f', '--first', type=click.IntRange(min=0, min_open=True),
              metavar="NUM", help="Print the first NUM lines.")
@click.option('-l', '--last', type=click.IntRange(min=0, min_open=True),
              metavar="NUM", help="Print the last NUM lines.")
@click.option('-t', '--timestamps', is_flag=True,
              help="Print lines that contain a timestamp in HH:MM:SS format.")
@click.option('-i', '--ipv4', is_flag=True,
              help="Print lines that contain an IPv4 address, " +
              "matching IPs are highlighted.")
@click.option('-I', '--ipv6', is_flag=True,
              help="Print lines that contain an IPv6 address," +
              "matching IPs are highlighted.")
@click.version_option(prog_name='util.py', package_name='pylogutil')
@click.argument('file', type=click.File('r'), metavar="[FILE]", default='-')
def clilogfilter(
        first: Optional[int],
        last: Optional[int],
        timestamps: bool,
        ipv4: bool,
        ipv6: bool,
        file: TextIO
) -> None:

    line_iter: Iterable[str] = file

    # create wrappers around `line_iter` to filter to the `first` and `last`
    # lines
    firstlast_filters: list[Iterable[str]] = []

    if first is not None:
        firstlast_filters.append(
            line for index, line in zip(range(first), line_iter))

    if last is not None:
        firstlast_filters.append(
            indirect_filter(collections.deque[str], line_iter, maxlen=last))

    if len(firstlast_filters) > 1:
        # chain the filters (back-to-back) if there is more than one
        line_iter = itertools.chain(*firstlast_filters)
    elif firstlast_filters:
        line_iter = firstlast_filters[0]

    # add regex-based filters around `line_iter` to filter out lines that do
    # not match any filter and add highlighting
    regex_filters: list[LineRegexFilter] = []

    if timestamps:
        regex_filters.append(timestamp_filter)
    if ipv4:
        regex_filters.append(ipv4_filter)
    if ipv6:
        regex_filters.append(ipv6_filter)

    if regex_filters:
        line_iter = filtermap(
            CompositeLineRegexFilter(*regex_filters), line_iter)

    # iterate over the the filtered lines and print them
    for line in line_iter:
        click.echo(line.rstrip('\n'))


def main() -> None:
    """Executes the `click` cli command `clifilter`."""
    clilogfilter()


if __name__ == '__main__':
    main()
