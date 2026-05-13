#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO, Iterator, Any
import struct
import field as FM


class SizedRecord:
    def __init__(self, fd: BinaryIO, numpoly: int):
        self.fd = fd
        self.numpoly = numpoly

    def iter_as(self, fmt: str | FM.FieldMeta) -> Iterator[Any]:
        for n in range(self.numpoly):
            (size,) = struct.unpack("<i", self.fd.read(4))
            if isinstance(fmt, str):
                for j in range(size // struct.calcsize("<dd")):
                    yield struct.unpack("<dd", self.fd.read(struct.calcsize("<dd")))
            elif isinstance(fmt, FM.FieldMeta):
                for j in range(size // fmt._view_size):
                    yield fmt(self.fd.read(fmt._view_size))


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = FM.PolyHeader(f.read(FM.PolyHeader._view_size))
        print(FM.as_tuple(ph))
        # print(ph.min.x)
        sr = SizedRecord(f, ph.numpoly)
        for pp in sr.iter_as("<dd"):
            print(pp)
    with open("polys.bin", "rb") as f:
        ph = FM.PolyHeader(f.read(FM.PolyHeader._view_size))
        sr = SizedRecord(f, ph.numpoly)
        for pp in sr.iter_as(FM.Point):
            print(pp)
