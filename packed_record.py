#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator, Any, BinaryIO
import struct
import field as FM


class PackedRecord:
    def __init__(self, bytes_data: bytes | memoryview):
        self._view = memoryview(bytes_data)

    @classmethod
    def from_file(cls, fd: BinaryIO, fmt: str, include_size: bool = True):
        buf: bytes
        sz_buf = fd.read(struct.calcsize("<i"))
        (size,) = struct.unpack("<i", sz_buf)
        if include_size:
            size -= struct.calcsize("<i")
        buf = fd.read(size)
        return cls(buf)

    def iter_as(self, fmt) -> Iterator[Any]:
        if isinstance(fmt, str):
            sz = struct.calcsize(fmt)

            def unpack(chunk):
                return struct.unpack_from(fmt, chunk)

        elif isinstance(fmt, FM.FieldMeta):
            sz = fmt._view_size
            unpack = fmt
        else:
            raise ValueError(f"{fmt} must be str of FieldMeta, got {type(fmt)!r}")
        for off in range(0, len(self._view), sz):
            o2 = off + sz
            yield unpack(self._view[off:o2])


if __name__ == "__main__":
    with open("polys.bin", "rb") as fd:
        ph = FM.PolyHeader(fd.read(FM.PolyHeader._view_size))
        for i in range(ph.numpoly):
            rec = PackedRecord.from_file(fd, "<i")
            for pp in rec.iter_as("<dd"):
                print(pp)
