#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import struct


class Field:
    """Descriptor"""

    def __init__(self, name: str, format: str, offset: int):
        self._name = name
        self.format = format
        self.offset = offset

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return struct.unpack_from(self.format, instance._view, self.offset)


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict):
        fields = clsdict["_fields"] if "_fields" in clsdict else {}
        offset: int = 0
        d = dict(clsdict)
        for field_name, fmt in fields:
            d[field_name] = Field(field_name, fmt, offset)
            offset += struct.calcsize(fmt)
        d["_view_size"] = offset
        return super().__new__(mcls, clsname, bases, d)


class View(metaclass=FieldMeta):
    def __init__(self, bytes_data):
        self._view = memoryview(bytes_data)


class PolyHeader(View):
    _fields = [
        ("code", "<i"),
        ("min_x", "<dd"),
        ("min_y", "<dd"),
        ("max_x", "<dd"),
        ("max_y", "<dd"),
        ("numpoly", "<i"),
    ]


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = PolyHeader(f.read(PolyHeader._view_size))
        print(ph.code)
