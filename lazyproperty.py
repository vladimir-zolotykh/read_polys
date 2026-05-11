#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Callable
import sys
import math
import pytest


class LazyProperty:
    """Describor"""

    def __init__(self, func: Callable):
        self.func = func
        self._name = func.__name__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        instance.__dict__[self._name] = val = self.func(instance)
        return val


class Circle:
    def __init__(self, radius):
        self.radius = radius

    @LazyProperty
    def area(self):
        print("Calculating area...")
        return math.pi * self.radius**2

    @LazyProperty
    def circumference(self):
        print("Calculating circumference...")
        return 2 * math.pi * self.radius


def test_lazyproperty(capsys):
    c = Circle(3.4)
    assert c.area == 36.316811075498
    captured = capsys.readouterr()
    assert "Calculating area...\n" in captured
    assert c.circumference == 21.362830044410593
    captured = capsys.readouterr()
    assert "Calculating circumference...\n" in captured


if __name__ == "__main__":
    pytest.main(sys.argv)
