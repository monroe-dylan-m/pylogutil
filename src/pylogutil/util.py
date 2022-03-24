"""Implements a console interface for interacting with logs.

.. data:: clilogfilter
    :type: click.Command

    .. automethod:: clilogfilter.callback

"""

from ._linefiltering._regexfilterbase import (LineRegexFilter,
                                              CompositeLineRegexFilter)
from ._linefilters import ipv4_filter, ipv6_filter, timestamp_filter
from ._misc import indirect_filter, filtermap
from typing import Iterable, Optional, TextIO
import click
import collections
import itertools

__all__ = ['clilogfilter', 'main']


@click.command(context_settings={'help_option_names': ['-h', '--help']},
               options_metavar="[OPTIONS...]",
               no_args_is_help=True,
               help="Prints the lines of a log file that match the " +
                    "criterion specified by OPTIONS.",
               epilog="If FILE is omitted, standard input is used instead.")
@click.option('-f', '--first',
              type=click.IntRange(min=0, min_open=True),
              metavar="NUM",
              help="Print the first NUM lines.")
@click.option('-l', '--last',
              type=click.IntRange(min=0, min_open=True),
              metavar="NUM",
              help="Print the last NUM lines.")
@click.option('-t', '--timestamps',
              is_flag=True,
              help="Print lines that contain a timestamp in HH:MM:SS format.")
@click.option('-i', '--ipv4',
              is_flag=True,
              help="Print lines that contain an IPv4 address, " +
              "matching IPs are highlighted.")
@click.option('-I', '--ipv6',
              is_flag=True,
              help="Print lines that contain an IPv6 address," +
              "matching IPs are highlighted.")
@click.version_option(prog_name='util.py',
                      package_name='pylogutil')
@click.argument('file',
                type=click.File('r'),
                metavar="[FILE]",
                default='-')
def clilogfilter(first: Optional[int],
                 last: Optional[int],
                 timestamps: bool,
                 ipv4: bool,
                 ipv6: bool,
                 file: TextIO
                 ) -> None:
    """Callback function for `clilogfilter` which receives the cli options 
    after `click` has processed them.

    Filters the input received from `file` according to the other parameters 
    and sends the resulting lines to stdout.

    Args:
        first: If not `None`, the number of lines from the start of the input 
            to include in the output.
        last: If not `None`, the number of lines from the end of the input to
            include in the output.
        timestamps: Whether to only include lines from the input containing a 
            timestamp in the output.
        ipv4: Whether to only include lines from the input containing an 
            IPv4 address in the output.
        ipv6: Whether to only include lines from the input containing an 
            IPv6 address the output.
        file: A file-like object opened for reading text (mode 'r') to be 
            used as input.
    """
    line_iter: Iterable[str] = file

    # create wrappers around `line_iter` to filter to the `first` and `last`
    # lines
    firstlast_filters: list[Iterable[str]] = []

    if first is not None:
        firstlast_filters.append(
            line for _, line in zip(range(first), line_iter))

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
    """Invokes `clilogfilter`."""
    clilogfilter()


if __name__ == '__main__':
    main()
