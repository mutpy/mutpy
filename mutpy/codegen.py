# -*- coding: utf-8 -*-
"""Wrapper module for astmonkey code generator."""

from astmonkey.visitors import to_source as astmonkey_to_source
import copy


def to_source(node, indent_with=' ' * 4):
    node = copy.deepcopy(node)
    return astmonkey_to_source(node=node, indent_with=indent_with)


def add_line_numbers(source):
    lines = source.split('\n')
    n = 0
    digits_number = len(str(len(lines)))

    while n < len(lines):
        lines[n] = '{:>{}}: {}'.format(n + 1, digits_number + 1, lines[n])
        n += 1

    return '\n'.join(lines)


def remove_extra_lines(source):
    parts = source.split('\n')
    result = [part for part in parts if part.strip()]
    return '\n'.join(result)
