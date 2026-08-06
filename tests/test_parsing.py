import pytest

from parsing import (
    ParsedTask,
    extract_assignee,
    get_arg_text,
    parse_shopping,
    parse_todo,
)


def test_extract_assignee_present():
    assert extract_assignee("@an Mua cà phê") == ("an", "Mua cà phê")


def test_extract_assignee_absent():
    assert extract_assignee("Mua cà phê") == (None, "Mua cà phê")


def test_parse_todo_with_assignee():
    t = parse_todo("@an Gọi khách hàng")
    assert t == ParsedTask(content="Gọi khách hàng", assignee="an")


def test_parse_todo_without_assignee():
    t = parse_todo("Dọn kho")
    assert t.content == "Dọn kho"
    assert t.assignee is None


def test_parse_todo_empty_raises():
    with pytest.raises(ValueError):
        parse_todo("@an   ")


def test_parse_shopping_full():
    t = parse_shopping("@an Sữa tươi | 2 | 25000")
    assert t.content == "Sữa tươi"
    assert t.assignee == "an"
    assert t.quantity == 2
    assert t.unit_price == 25000


def test_parse_shopping_name_only():
    t = parse_shopping("Bánh mì")
    assert t.content == "Bánh mì"
    assert t.quantity is None
    assert t.unit_price is None


def test_parse_shopping_strips_dot_thousands():
    t = parse_shopping("Gạo | 1 | 25.000")
    assert t.unit_price == 25000


def test_parse_shopping_bad_number_raises():
    with pytest.raises(ValueError):
        parse_shopping("Táo | hai | 1000")


def test_parse_shopping_empty_name_raises():
    with pytest.raises(ValueError):
        parse_shopping("  |  | 1000")


def test_get_arg_text():
    assert get_arg_text("/list @an Mua cà phê") == "@an Mua cà phê"
    assert get_arg_text("/list") == ""
    assert get_arg_text("/list@MyBot Dọn kho") == "Dọn kho"


def test_parse_shopping_decimal_comma():
    t = parse_shopping("Thịt | 0,5 | 100000")
    assert t.quantity == 0.5
    assert t.unit_price == 100000


def test_parse_shopping_comma_decimal_with_dot_thousands():
    t = parse_shopping("Gạo | 1,5 | 25.000")
    assert t.quantity == 1.5
    assert t.unit_price == 25000


def test_parse_shopping_rejects_non_finite():
    import pytest
    with pytest.raises(ValueError):
        parse_shopping("X | inf | 1000")
