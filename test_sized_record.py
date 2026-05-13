#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
# test_sized_record.py
import io
import struct

import pytest

import field as FM
from sized_record import SizedRecord


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def pack_record(points):
    """
    Pack one polygon record.

    Format:
        <i>   size in bytes
        data  repeated <dd>
    """
    payload = b"".join(struct.pack("<dd", x, y) for x, y in points)
    return struct.pack("<i", len(payload)) + payload


# ------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------


@pytest.fixture
def polygon_data():
    """
    Creates binary stream containing two polygon records.

    poly1:
        (1, 2)
        (3, 4)

    poly2:
        (10, 20)
    """
    poly1 = pack_record(
        [
            (1.0, 2.0),
            (3.0, 4.0),
        ]
    )

    poly2 = pack_record(
        [
            (10.0, 20.0),
        ]
    )

    return poly1 + poly2


@pytest.fixture
def fd(polygon_data):
    return io.BytesIO(polygon_data)


@pytest.fixture
def sized_record(fd):
    return SizedRecord(fd, numpoly=2)


# ------------------------------------------------------------
# Construction
# ------------------------------------------------------------


def test_constructor_stores_attributes(fd):
    sr = SizedRecord(fd, 123)

    assert sr.fd is fd
    assert sr.numpoly == 123


# ------------------------------------------------------------
# iter_as with struct format
# ------------------------------------------------------------


def test_iter_as_tuple_format(sized_record):
    result = list(sized_record.iter_as("<dd"))

    assert result == [
        (1.0, 2.0),
        (3.0, 4.0),
        (10.0, 20.0),
    ]


def test_iter_as_returns_iterator(sized_record):
    it = sized_record.iter_as("<dd")

    assert iter(it) is it


def test_iter_as_empty_when_numpoly_zero(fd):
    sr = SizedRecord(fd, 0)

    result = list(sr.iter_as("<dd"))

    assert result == []


# ------------------------------------------------------------
# iter_as with View type
# ------------------------------------------------------------


def test_iter_as_point_objects(sized_record):
    result = list(sized_record.iter_as(FM.Point))

    assert len(result) == 3

    assert all(isinstance(x, FM.Point) for x in result)

    assert result[0].x == 1.0
    assert result[0].y == 2.0

    assert result[1].x == 3.0
    assert result[1].y == 4.0

    assert result[2].x == 10.0
    assert result[2].y == 20.0


def test_iter_as_point_repr(sized_record):
    result = list(sized_record.iter_as(FM.Point))

    assert repr(result[0]) == "(1.0, 2.0)"
    assert repr(result[1]) == "(3.0, 4.0)"
    assert repr(result[2]) == "(10.0, 20.0)"


# ------------------------------------------------------------
# Binary layout tests
# ------------------------------------------------------------


def test_reads_exact_amount_of_data(polygon_data):
    fd = io.BytesIO(polygon_data)

    sr = SizedRecord(fd, 2)

    result = list(sr.iter_as("<dd"))

    assert len(result) == 3

    # stream must be exhausted
    assert fd.read() == b""


def test_partial_iteration_leaves_stream_position(polygon_data):
    fd = io.BytesIO(polygon_data)

    sr = SizedRecord(fd, 2)

    it = sr.iter_as("<dd")

    first = next(it)

    assert first == (1.0, 2.0)

    # stream position should advance
    assert fd.tell() > 0


# ------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------


def test_empty_polygon_record():
    data = struct.pack("<i", 0)

    fd = io.BytesIO(data)

    sr = SizedRecord(fd, 1)

    result = list(sr.iter_as("<dd"))

    assert result == []


def test_incomplete_size_field_raises():
    fd = io.BytesIO(b"\x01\x02")

    sr = SizedRecord(fd, 1)

    with pytest.raises(struct.error):
        list(sr.iter_as("<dd"))


def test_incomplete_point_payload_raises():
    payload = struct.pack("<i", 16)
    payload += b"\x00" * 8

    fd = io.BytesIO(payload)

    sr = SizedRecord(fd, 1)

    with pytest.raises(struct.error):
        list(sr.iter_as("<dd"))


# ------------------------------------------------------------
# Mixed polygon sizes
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "polygons, expected_count",
    [
        ([], 0),
        ([[(1.0, 2.0)]], 1),
        ([[(1.0, 2.0), (3.0, 4.0)]], 2),
        (
            [
                [(1.0, 2.0)],
                [(3.0, 4.0), (5.0, 6.0)],
            ],
            3,
        ),
    ],
)
def test_various_polygon_counts(polygons, expected_count):
    data = b"".join(pack_record(poly) for poly in polygons)

    fd = io.BytesIO(data)

    sr = SizedRecord(fd, len(polygons))

    result = list(sr.iter_as("<dd"))

    assert len(result) == expected_count
