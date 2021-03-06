pylogutil
=========

Basic log filter in python

Installation
------------

1. Clone this repo.
2. Navigate into the repo root directory.
3. **(Recommended)** Set up a virtual environment here using venv::

    python -m venv .venv

4. Run ``pip install .``
5. Run the cli application using ``util.py`` (see `Usage`_, below).

Usage
------

::

    Usage: util.py [OPTIONS...] [FILE]

    Prints the lines of a log file that match the criterion specified by
    OPTIONS.

    Options:
    -f, --first NUM   Print the first NUM lines.  [x>0]
    -l, --last NUM    Print the last NUM lines.  [x>0]
    -t, --timestamps  Print lines that contain a timestamp in HH:MM:SS format.
    -i, --ipv4        Print lines that contain an IPv4 address, matching IPs are
                        highlighted.
    -I, --ipv6        Print lines that contain an IPv6 address,matching IPs are
                        highlighted.
    --version         Show the version and exit.
    -h, --help        Show this message and exit.

    If FILE is omitted, standard input is used instead.
