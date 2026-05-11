#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Callable
import math


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


if __name__ == "__main__":
    c = Circle(3.4)
    print(c.area)
    print(c.circumference)
