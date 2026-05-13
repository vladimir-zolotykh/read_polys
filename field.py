#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import ClassVar
import struct


class Field:
    """Descriptor"""

    def __init__(self, name: str, fmt_or_view: str, offset: int):
        self._name = name
        self.fmt_or_view = fmt_or_view
        self.offset = offset

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if isinstance(self.fmt_or_view, str):
            tup = struct.unpack_from(self.fmt_or_view, instance._view, self.offset)
            return tup[0] if len(tup) == 1 else tup
        elif isinstance(self.fmt_or_view, FieldMeta):
            view_type = self.fmt_or_view
            o1 = self.offset
            o2 = self.offset + view_type._view_size
            return view_type(instance._view[o1:o2])
        else:
            raise TypeError(f"{self.fmt_or_view}: must be str or View")


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict):
        fields = clsdict["_fields"] if "_fields" in clsdict else {}
        offset: int = 0
        d = dict(clsdict)
        for field_name, fmt_or_type in fields:
            if isinstance(fmt_or_type, str):
                fmt = fmt_or_type
                d[field_name] = Field(field_name, fmt, offset)
                offset += struct.calcsize(fmt)
            # elif issubclass(fmt_or_type, View):
            elif isinstance(fmt_or_type, FieldMeta):
                view_type = fmt_or_type
                d[field_name] = Field(field_name, view_type, offset)
                offset += view_type._view_size
            else:
                raise TypeError(f"{fmt_or_type}: must be str or View")
        d["_view_size"] = offset
        return super().__new__(mcls, clsname, bases, d)


class View(metaclass=FieldMeta):
    _view_size: ClassVar[int]
    _fields: ClassVar[list[tuple[str, str]]]

    def __init__(self, bytes_data):
        self._view = memoryview(bytes_data)


class Point(View):
    _fields = [
        ("x", "<d"),
        ("y", "<d"),
    ]

    def __repr__(self):
        return f'({getattr(self, "x")}, {getattr(self, "y")})'


class PolyHeader(View):
    _fields = [
        ("code", "<i"),
        ("min", Point),
        ("max", Point),
        ("numpoly", "<i"),
    ]


def as_tuple(view: View) -> str:
    return ", ".join(f"{fld[0]}={str(getattr(view, fld[0]))}" for fld in view._fields)


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = PolyHeader(f.read(PolyHeader._view_size))
        print(as_tuple(ph))
        # print(ph.min.x)
