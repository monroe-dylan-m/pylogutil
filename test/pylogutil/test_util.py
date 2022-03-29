"""Contains tests for the `pylogutil.util` cli application."""

from dataclasses import dataclass
from typing import Optional, Sequence
from typing_extensions import Self
import click
from click.testing import CliRunner, Result
from pylogutil.util import clilogfilter
from pylogutil._linefiltering._colorgen import RgbConverter
import pytest


@dataclass
class CliArgs:
    """Stores arguments for the `pylogutil.util` cli application."""

    help: bool = False
    version: bool = False
    first: Optional[int] = None
    last: Optional[int] = None
    timestamps: bool = False
    ipv4: bool = False
    ipv6: bool = False
    file: Optional[str] = None

    def to_arg_list(self: Self) -> Sequence[str]:
        """Converts all argument values into a list of strings which can 
        be used to invoke `clilogfilter` with the same arguments."""

        args: list[str] = []

        if self.help:
            args.append('--help')
        if self.version:
            args.append('--version')
        if self.first is not None:
            args.extend(['--first', str(self.first)])
        if self.last is not None:
            args.extend(['--last', str(self.last)])
        if self.timestamps:
            args.append('--timestamps')
        if self.ipv4:
            args.append('--ipv4')
        if self.ipv6:
            args.append('--ipv6')
        if self.file is not None:
            args.extend(['--file', self.file])

        return args


@dataclass
class Expect:
    """Represents the expected outcome of a cli application"""

    exit_code: Optional[int] = 0
    stdout: Optional[str] = None
    stderr: Optional[str] = None


def line_number_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``Line 1``, ``Line 2``, ...

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """

    return ''.join(f'Line {i}\n'
                   for i in range(1 + start, 1 + start + nlines))


def timestamp_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``[12:34:01]: Timestamp``, ``[12:34:02]: Timestamp``, ...

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join(f'[12:34:{i%100:02}]: Timestamp\n'
                   for i in range(1 + start, 1 + start + nlines))


def timestamp_styled_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``[12:34:01]: Timestamp``, ``[12:34:02]: Timestamp``, ...
    Includes text styling.

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join('[' +
                   click.style(f'12:34:{i%100:02}',
                               bold=True,
                               fg='bright_white') +
                   ']: Timestamp\n'
                   for i in range(1 + start, 1 + start + nlines))


def ipv4_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``An IPv4: 192.168.1.1``, ``An IPv4: 192.168.1.2``, ...

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join(f'An IPv4: 192.168.1.{i%256}\n'
                   for i in range(1 + start, 1 + start + nlines))


def ipv4_styled_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``An IPv4: 192.168.1.1``, ``An IPv4: 192.168.1.2``, ...
    Includes text styling.

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join('An IPv4: ' +
                   click.style(f'192.168.1.{i%256}',
                               underline=True,
                               fg=RgbConverter.from_int_list_8bit([
                                   192, 168, 1, i % 256
                               ])) + '\n'
                   for i in range(1 + start, 1 + start + nlines))


def ipv6_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``An IPv6: fe80:12::34:1``, ``An IPv6: fe80:12::34:2``, ...

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join(f'An IPv6: fe80:12::34:{i % 0x1000 :x}\n'
                   for i in range(1 + start, 1 + start + nlines))


def ipv6_styled_log(nlines: int, start: int = 0) -> str:
    """Generates a log file string with `nlines` lines in the format: 
    ``An IPv6: fe80:12::34:1``, ``An IPv6: fe80:12::34:2``, ...
    Includes text styling.

    Args:
        nlines: The number of lines.
        start: the line number to start on.

    Returns:
        A string where each line is followed by a newline character (``\\n``).
    """
    return ''.join('An IPv6: ' +
                   click.style(f'fe80:12::34:{i % 0x1000 :x}',
                               underline=True,
                               fg=RgbConverter.from_int_list_8bit([
                                   0xfe80, 0x12, 0, 0,
                                   0, 0, 0x34, i % 0x1000
                               ])) + '\n'
                   for i in range(1 + start, 1 + start + nlines))


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


class Invoker():
    """Invokes the `pylogutil.util` cli application using the supplied
    arguments."""

    _runner: CliRunner

    def __init__(self: Self, runner: CliRunner) -> None:
        self._runner = runner

    def __call__(self: Self,
                 args: CliArgs,
                 stdin: Optional[str] = None,
                 expect: Expect = Expect(),
                 color: bool = True
                 ) -> Result:
        """
        Args:
            args: The application arguments.
            stdin: If not `None`, the application's stdin. Defaults to `None`.
            expect: The expected application result.
                Defaults to a default `Expect` instance.
            color: Whether application output should include color codes.
                Defaults to `True`.

        Returns:
            The cli application result.
        """

        result: Result = self._runner.invoke(
            clilogfilter, args.to_arg_list(), stdin, color=color)

        if expect.exit_code is not None:
            assert result.exit_code == expect.exit_code

        if expect.stdout is not None:
            assert result.stdout == expect.stdout

        if expect.stderr is not None:
            assert result.stderr == expect.stderr

        return result


@pytest.fixture(scope="module")
def invoker(runner: CliRunner) -> Invoker:
    return Invoker(runner)


@pytest.mark.parametrize(
    ('first', 'stdin', 'expected_value'),
    [
        pytest.param(7, line_number_log(7),
                     line_number_log(7),
                     id='1_first-equals-length'),

        pytest.param(7, line_number_log(10),
                     line_number_log(7),
                     id='2_first-lessthan-length'),

        pytest.param(7, line_number_log(6),
                     line_number_log(6),
                     id='3_first-greaterthan-length'),

        pytest.param(7, '',
                     '',
                     id='4_first-nonzero_empty-log'),

        pytest.param(7, '\n',
                     '\n',
                     id='5_first-nonzero_one-blank-line-log'),

        pytest.param(0, None,
                     2,
                     id='6_first-zero'),

        pytest.param(-7, None,
                     2,
                     id='7_first-negative'),
    ]
)
def test_first(invoker: Invoker,
               first: int,
               stdin: Optional[str],
               expected_value: str | int
               ) -> None:
    invoker(
        CliArgs(first=first),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))


@pytest.mark.parametrize(
    ('last', 'stdin', 'expected_value'),
    [
        pytest.param(7, line_number_log(7),
                     line_number_log(7),
                     id='1_last-equals-length'),

        pytest.param(7, line_number_log(10),
                     line_number_log(7, 10-7),
                     id='2_last-lessthan-length'),

        pytest.param(7, line_number_log(6),
                     line_number_log(6),
                     id='3_last-greaterthan-length'),

        pytest.param(7, '',
                     '',
                     id='4_last-nonzero_empty-log'),

        pytest.param(7, '\n',
                     '\n',
                     id='5_last-nonzero_one-blank-line-log'),

        pytest.param(0, None,
                     2,
                     id='6_last-zero'),

        pytest.param(-7, None,
                     2,
                     id='7_last-negative'),
    ]
)
def test_last(invoker: Invoker,
              last: int,
              stdin: Optional[str],
              expected_value: str | int
              ) -> None:
    invoker(
        CliArgs(last=last),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))


@pytest.mark.parametrize(
    ('first', 'last', 'stdin', 'expected_value'),
    [
        pytest.param(2, 4, line_number_log(7),
                     (line_number_log(2) + line_number_log(4, 3)),
                     id='1_first-plus-last-lessthan-length'),

        pytest.param(3, 4, line_number_log(7),
                     line_number_log(7),
                     id='2_first-plus-last-equalto-length'),

        pytest.param(4, 4, line_number_log(7),
                     line_number_log(7),
                     id='3_first-plus-last-lessthan-length'),
    ]
)
def test_firstlast(invoker: Invoker,
                   first: int,
                   last: int,
                   stdin: Optional[str],
                   expected_value: str | int
                   ) -> None:
    invoker(
        CliArgs(first=first, last=last),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))


@pytest.mark.parametrize(
    ('stdin', 'expected_value'),
    [
        pytest.param(timestamp_log(7),
                     timestamp_styled_log(7),
                     id='1_all-lines-match'),

        pytest.param((line_number_log(2) +
                      timestamp_log(3) +
                      line_number_log(2, 6)),
                     timestamp_styled_log(3),
                     id='2_middle-lines-match'),

        pytest.param((timestamp_log(2) +
                      line_number_log(3, 3) +
                      timestamp_log(2)),
                     (timestamp_styled_log(2) +
                      timestamp_styled_log(2)),
                     id='3_start-and-end-lines-match'),
    ]
)
def test_timestamps(invoker: Invoker,
                    stdin: Optional[str],
                    expected_value: str | int
                    ) -> None:
    invoker(
        CliArgs(timestamps=True),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))


@pytest.mark.parametrize(
    ('stdin', 'expected_value'),
    [
        pytest.param(ipv4_log(7),
                     ipv4_styled_log(7),
                     id='1_all-lines-match'),

        pytest.param((line_number_log(2) +
                      ipv4_log(3) +
                      line_number_log(2, 6)),
                     ipv4_styled_log(3),
                     id='2_middle-lines-match'),

        pytest.param((ipv4_log(2) +
                      line_number_log(3, 3) +
                      ipv4_log(2)),
                     (ipv4_styled_log(2) +
                      ipv4_styled_log(2)),
                     id='3_start-and-end-lines-match'),
    ]
)
def test_ipv4(invoker: Invoker,
              stdin: Optional[str],
              expected_value: str | int
              ) -> None:
    invoker(
        CliArgs(ipv4=True),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))


@pytest.mark.parametrize(
    ('stdin', 'expected_value'),
    [
        pytest.param(ipv6_log(7),
                     ipv6_styled_log(7),
                     id='1_all-lines-match'),

        pytest.param((line_number_log(2) +
                      ipv6_log(3) +
                      line_number_log(2, 6)),
                     ipv6_styled_log(3),
                     id='2_middle-lines-match'),

        pytest.param((ipv6_log(2) +
                      line_number_log(3, 3) +
                      ipv6_log(2)),
                     (ipv6_styled_log(2) +
                      ipv6_styled_log(2)),
                     id='3_start-and-end-lines-match'),
    ]
)
def test_ipv6(invoker: Invoker,
              stdin: Optional[str],
              expected_value: str | int
              ) -> None:
    invoker(
        CliArgs(ipv6=True),
        stdin,
        Expect(**{
            ('exit_code' if isinstance(expected_value, int) else 'stdout'):
                expected_value}))
