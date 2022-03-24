"""Implements functionality to map data to color codes."""

from typing import Final, Sequence
from typing_extensions import Self

__all__ = ['RgbConverter']


class RgbConverter:
    """A utility class to convert lists of integers into colors. Currently 
    used to calculate the highlight colors for the ipv4 and ipv6 filters."""
    _min24: Final[int] = 70
    _max24: Final[int] = 255
    _range24: Final[int] = _min24 - _max24

    # all 8-bit colors with greyscale colors removed
    # specifically: 0, 7, 15, 231-255
    _value_table_8bit: Final[Sequence[int]] = tuple(
        x for x in range(256) if x not in (
            0, 7, 15, *range(231, 256)))

    _range8: int = len(_value_table_8bit)

    @classmethod
    def from_int_list_24bit(cls: type[Self],
                            lst: Sequence[int]
                            ) -> tuple[int, int, int]:

        rgb_out = [0, 0, 0]
        extra_count = len(lst) % 3
        even_count = len(lst) - extra_count

        for i in range(even_count):
            rgb_out[i % 3] = (
                rgb_out[i % 3] + lst[i] + hash(i)
            ) % cls._range24

        for i in range(extra_count):
            amount: int = (
                (lst[even_count + i] + hash(even_count + i)) // 3
            ) % cls._range24

            rgb_out[0] += amount
            rgb_out[1] += amount
            rgb_out[2] += amount

        rgb_out[0] += cls._min24
        rgb_out[1] += cls._min24
        rgb_out[2] += cls._min24

        return (rgb_out[0], rgb_out[1], rgb_out[2])

    @classmethod
    def from_int_list_8bit(cls: type[Self], lst: Sequence[int]) -> int:

        rgb_out = 0

        for i in lst:
            rgb_out = (rgb_out + i) % cls._range8

        return cls._value_table_8bit[rgb_out]
