from typing import NoReturn
import click

@click.command(context_settings={'help_option_names': ['-h','--help']}, options_metavar="[OPTIONS...]", help="Prints the lines of FILE (or stdin if no file is specified) after applying the filters specified by OPTIONS.")

@click.option('-f','--first', type=click.IntRange(min=0,min_open=True), metavar="NUM", help="Print the first NUM lines.")
@click.option('-l','--last', type=click.IntRange(min=0,min_open=True), metavar="NUM", help="Print the last NUM lines.")
@click.option('-t','--timestamps', help="Print lines that contain a timestamp in HH:MM:SS format.", is_flag=True)
@click.option('-i','--ipv4', help="Print lines that contain an IPv4 address, matching IPs are highlighted.", is_flag=True)
@click.option('-I','--ipv6', help="Print lines that contain an IPv6 address, matching IPs are highlighted.", is_flag=True)
@click.version_option(prog_name='util.py', package_name='pylogutil')

@click.argument('file', type=click.Path(exists=True,dir_okay=False), metavar="[FILE]", required=False)

def main(first: int, last: int, timestamps: bool, ipv4: bool, ipv6: bool, file: str) -> NoReturn:
    click.echo(message=f"first={first}")
    click.echo(message=f"last={last}")
    click.echo(message=f"timestamps={timestamps}")
    click.echo(message=f"ipv4={ipv4}")
    click.echo(message=f"ipv6={ipv6}")
    click.echo(message=f"file={file}")

if __name__ == '__main__':
    main()