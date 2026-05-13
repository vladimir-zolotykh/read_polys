#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
# test_views.py
import struct
import pytest

from field import (
    Field,
    FieldMeta,
    View,
    Point,
    PolyHeader,
    as_tuple,
)


@pytest.fixture
def point_bytes():
    return struct.pack("<dd", 1.5, -2.25)


@pytest.fixture
def point(point_bytes):
    return Point(point_bytes)


@pytest.fixture
def polyheader_bytes():
    return struct.pack(
        "<i"  # code
        "dd"  # min point
        "dd"  # max point
        "i",  # numpoly
        7,
        1.0,
        2.0,
        10.0,
        20.0,
        42,
    )


@pytest.fixture
def polyheader(polyheader_bytes):
    return PolyHeader(polyheader_bytes)


# ------------------------------------------------------------
# Point tests
# ------------------------------------------------------------


def test_point_fields(point):
    assert point.x == 1.5
    assert point.y == -2.25


def test_point_repr(point):
    assert repr(point) == "(1.5, -2.25)"


def test_point_view_size():
    assert Point._view_size == struct.calcsize("<dd")


def test_point_memoryview_storage(point_bytes):
    p = Point(point_bytes)
    assert isinstance(p._view, memoryview)


# ------------------------------------------------------------
# PolyHeader tests
# ------------------------------------------------------------


def test_polyheader_scalar_fields(polyheader):
    assert polyheader.code == 7
    assert polyheader.numpoly == 42


def test_polyheader_nested_min_point(polyheader):
    assert isinstance(polyheader.min, Point)
    assert polyheader.min.x == 1.0
    assert polyheader.min.y == 2.0


def test_polyheader_nested_max_point(polyheader):
    assert isinstance(polyheader.max, Point)
    assert polyheader.max.x == 10.0
    assert polyheader.max.y == 20.0


def test_polyheader_returns_new_view_instances(polyheader):
    m1 = polyheader.min
    m2 = polyheader.min

    assert isinstance(m1, Point)
    assert isinstance(m2, Point)
    assert m1 is not m2


def test_polyheader_offsets():
    assert PolyHeader.code.offset == 0

    assert PolyHeader.min.offset == struct.calcsize("<i")

    assert PolyHeader.max.offset == (struct.calcsize("<i") + Point._view_size)

    assert PolyHeader.numpoly.offset == (struct.calcsize("<i") + Point._view_size * 2)


def test_polyheader_view_size():
    expected = (
        struct.calcsize("<i")
        + Point._view_size
        + Point._view_size
        + struct.calcsize("<i")
    )
    assert PolyHeader._view_size == expected


def test_polyheader_as_tuple(polyheader):
    s = as_tuple(polyheader)

    assert "code=7" in s
    assert "min=(1.0, 2.0)" in s
    assert "max=(10.0, 20.0)" in s
    assert "numpoly=42" in s


# ------------------------------------------------------------
# Descriptor behavior
# ------------------------------------------------------------


def test_descriptor_access_on_class():
    assert isinstance(Point.x, Field)
    assert isinstance(Point.y, Field)


def test_descriptor_name_assignment():
    assert Point.x._name == "x"
    assert Point.y._name == "y"


def test_field_descriptor_unpacking():
    data = struct.pack("<d", 123.456)

    class Single(View):
        _fields = [
            ("value", "<d"),
        ]

    s = Single(data)

    assert s.value == pytest.approx(123.456)


# ------------------------------------------------------------
# Metaclass validation
# ------------------------------------------------------------


def test_invalid_field_type_raises_typeerror():
    with pytest.raises(TypeError):

        class BadView(View):
            _fields = [
                ("bad", int),
            ]


def test_nested_view_field_definition():
    class Line(View):
        _fields = [
            ("p1", Point),
            ("p2", Point),
        ]

    expected = Point._view_size * 2
    assert Line._view_size == expected


# ------------------------------------------------------------
# Binary integrity tests
# ------------------------------------------------------------


def test_polyheader_reads_exact_binary_layout(polyheader_bytes):
    ph = PolyHeader(polyheader_bytes)

    raw_code = struct.unpack_from("<i", polyheader_bytes, 0)[0]
    assert ph.code == raw_code

    raw_min_x = struct.unpack_from("<d", polyheader_bytes, 4)[0]
    assert ph.min.x == raw_min_x

    raw_max_y = struct.unpack_from(
        "<d",
        polyheader_bytes,
        4 + Point._view_size + 8,
    )[0]

    assert ph.max.y == raw_max_y


def test_short_buffer_raises_struct_error():
    short_data = b"\x00\x01"

    p = Point(short_data)

    with pytest.raises(struct.error):
        _ = p.x
