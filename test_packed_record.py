#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
# test_packed_record.py
import io
import struct

import pytest

import field as FM
from packed_record import PackedRecord


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def pack_points(points):
    """
    Pack sequence of (x, y) tuples as repeated <dd>.
    """
    return b"".join(struct.pack("<dd", x, y) for x, y in points)


def make_record(points, include_size=True):
    """
    Create one binary record.

    Record layout:
        <i> size
        payload
    """
    payload = pack_points(points)

    if include_size:
        size = len(payload) + struct.calcsize("<i")
    else:
        size = len(payload)

    return struct.pack("<i", size) + payload


# ------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------


@pytest.fixture
def simple_points():
    return [
        (1.0, 2.5),
        (3.5, 4.0),
    ]


@pytest.fixture
def simple_payload(simple_points):
    return pack_points(simple_points)


@pytest.fixture
def packed_record(simple_payload):
    return PackedRecord(simple_payload)


# ------------------------------------------------------------
# Construction
# ------------------------------------------------------------


def test_constructor_stores_memoryview(simple_payload):
    rec = PackedRecord(simple_payload)

    assert isinstance(rec._view, memoryview)


def test_constructor_accepts_memoryview(simple_payload):
    mv = memoryview(simple_payload)

    rec = PackedRecord(mv)

    assert isinstance(rec._view, memoryview)


# ------------------------------------------------------------
# from_file()
# ------------------------------------------------------------


def test_from_file_reads_payload(simple_points):
    data = make_record(simple_points)

    fd = io.BytesIO(data)

    rec = PackedRecord.from_file(fd, "<i")

    result = list(rec.iter_as("<dd"))

    assert result == [
        (1.0, 2.5),
        (3.5, 4.0),
    ]


def test_from_file_include_size_false(simple_points):
    data = make_record(simple_points, include_size=False)

    fd = io.BytesIO(data)

    rec = PackedRecord.from_file(
        fd,
        "<i",
        include_size=False,
    )

    result = list(rec.iter_as("<dd"))

    assert result == [
        (1.0, 2.5),
        (3.5, 4.0),
    ]


def test_from_file_advances_stream_position(simple_points):
    data = make_record(simple_points)

    fd = io.BytesIO(data)

    PackedRecord.from_file(fd, "<i")

    assert fd.tell() == len(data)


def test_from_file_incomplete_size_field_raises():
    fd = io.BytesIO(b"\x01\x02")

    with pytest.raises(struct.error):
        PackedRecord.from_file(fd, "<i")


# ------------------------------------------------------------
# iter_as() with struct formats
# ------------------------------------------------------------


def test_iter_as_struct_format(packed_record):
    result = list(packed_record.iter_as("<dd"))

    assert result == [
        (1.0, 2.5),
        (3.5, 4.0),
    ]


def test_iter_as_returns_iterator(packed_record):
    it = packed_record.iter_as("<dd")

    assert iter(it) is it


def test_iter_as_single_item():
    payload = struct.pack("<dd", 7.0, 8.0)

    rec = PackedRecord(payload)

    result = list(rec.iter_as("<dd"))

    assert result == [
        (7.0, 8.0),
    ]


def test_iter_as_empty_payload():
    rec = PackedRecord(b"")

    result = list(rec.iter_as("<dd"))

    assert result == []


# ------------------------------------------------------------
# iter_as() with FieldMeta
# ------------------------------------------------------------


def test_iter_as_point_objects(packed_record):
    result = list(packed_record.iter_as(FM.Point))

    assert len(result) == 2

    assert all(isinstance(x, FM.Point) for x in result)


def test_iter_as_point_values(packed_record):
    result = list(packed_record.iter_as(FM.Point))

    assert result[0].x == 1.0
    assert result[0].y == 2.5

    assert result[1].x == 3.5
    assert result[1].y == 4.0


# ------------------------------------------------------------
# Error handling
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_fmt",
    [
        123,
        3.14,
        object(),
        list,
        None,
    ],
)
def test_iter_as_invalid_format_raises(packed_record, bad_fmt):
    with pytest.raises(ValueError):
        list(packed_record.iter_as(bad_fmt))


def test_iter_as_incomplete_chunk_raises():
    payload = b"\x00" * 8

    rec = PackedRecord(payload)

    with pytest.raises(struct.error):
        list(rec.iter_as("<dd"))


# ------------------------------------------------------------
# Binary correctness
# ------------------------------------------------------------


def test_iter_as_reads_exact_chunks():
    payload = (
        struct.pack("<dd", 1.0, 2.0)
        + struct.pack("<dd", 3.0, 4.0)
        + struct.pack("<dd", 5.0, 6.0)
    )

    rec = PackedRecord(payload)

    result = list(rec.iter_as("<dd"))

    assert len(result) == 3

    assert result[2] == (5.0, 6.0)


def test_iter_as_point_chunk_boundaries():
    payload = struct.pack("<dd", 10.0, 20.0) + struct.pack("<dd", 30.0, 40.0)

    rec = PackedRecord(payload)

    pts = list(rec.iter_as(FM.Point))

    assert pts[0].x == 10.0
    assert pts[0].y == 20.0

    assert pts[1].x == 30.0
    assert pts[1].y == 40.0


# ------------------------------------------------------------
# Mixed records similar to __main__
# ------------------------------------------------------------


def test_multiple_records_mixed_formats():
    rec1 = make_record(
        [
            (1.0, 2.5),
            (3.5, 4.0),
        ]
    )

    rec2 = make_record(
        [
            (7.0, 1.2),
            (5.1, 3.0),
        ]
    )

    rec3 = make_record(
        [
            (3.4, 6.3),
        ]
    )

    fd = io.BytesIO(rec1 + rec2 + rec3)

    r1 = PackedRecord.from_file(fd, "<i")
    r2 = PackedRecord.from_file(fd, "<i")
    r3 = PackedRecord.from_file(fd, "<i")

    assert list(r1.iter_as("<dd")) == [
        (1.0, 2.5),
        (3.5, 4.0),
    ]

    pts = list(r2.iter_as(FM.Point))

    assert pts[0].x == 7.0
    assert pts[0].y == 1.2

    assert pts[1].x == 5.1
    assert pts[1].y == 3.0

    assert list(r3.iter_as("<dd")) == [
        (3.4, 6.3),
    ]
