#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator, Any, BinaryIO
import struct
import FieldMeta as FM


class PackedRecord:
    def __init__(self, bytes_data: bytes | memoryview):
        self._view = memoryview(bytes_data)

    @classmethod
    def from_file(cls, fd: BinaryIO, fmt: str, include_size: bool = True):
        buf: bytes
        sz_buf = fd.read(struct.calcsize("<i"))
        (size,) = struct.unpack("<i", sz_buf)
        if include_size:
            size -= sz_buf
        buf = fd.read(size)
        return cls(buf)

    def iter_as(self, fmt) -> Iterator[Any]:
        if isinstance(fmt, str):
            sz = struct.calcsize(fmt)
        elif isinstance(fmt, FM.FieldMeta):
            sz = fmt._view_size
        else:
            raise ValueError(f"{fmt} must be str of FieldMeta")
        for off in range(0, len(self._view), sz):
            o2 = off + sz
            if isinstance(fmt, str):
                yield struct.unpack_from(fmt, self._view[off:o2])
            else:
                yield fmt(self._view[off:o2])


if __name__ == "__main__":
    with open("polys.bin", "rb") as fd:
        ph = FM.PolyHeader(fd.read(FM.PolyHeader._view_size))
        for i in range(ph.numpolys):
            rec = PackedRecord.from_file("<i")
            for pp in rec.iter_as("<dd"):
                print(pp)
