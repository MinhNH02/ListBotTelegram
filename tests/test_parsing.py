import pytest

from parsing import (
    ParsedTask,
    extract_assignee,
    get_arg_text,
    parse_lines,
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


def test_parse_shopping_with_description():
    t = parse_shopping("@minh Mua ức gà | 400g ức gà")
    assert t.content == "Mua ức gà"
    assert t.assignee == "minh"
    assert t.description == "400g ức gà"


def test_parse_shopping_name_only():
    t = parse_shopping("Bánh mì")
    assert t.content == "Bánh mì"
    assert t.description is None


def test_parse_shopping_description_can_contain_pipe():
    t = parse_shopping("Mua đồ | 1 gói | còn dư thì để tủ lạnh")
    assert t.content == "Mua đồ"
    assert t.description == "1 gói | còn dư thì để tủ lạnh"


def test_parse_shopping_empty_name_raises():
    with pytest.raises(ValueError):
        parse_shopping("  | 400g ức gà")


def test_get_arg_text():
    assert get_arg_text("/list @an Mua cà phê") == "@an Mua cà phê"
    assert get_arg_text("/list") == ""
    assert get_arg_text("/list@MyBot Dọn kho") == "Dọn kho"


def test_parse_lines_single_line_todo():
    tasks, errors = parse_lines("@an Mua cà phê", "todo")
    assert tasks == [ParsedTask(content="Mua cà phê", assignee="an")]
    assert errors == []


def test_parse_lines_multi_line_todo_mixed_assignee():
    arg = "@an Mua cà phê\n@minh Gọi khách hàng\nDọn kho"
    tasks, errors = parse_lines(arg, "todo")
    assert tasks == [
        ParsedTask(content="Mua cà phê", assignee="an"),
        ParsedTask(content="Gọi khách hàng", assignee="minh"),
        ParsedTask(content="Dọn kho", assignee=None),
    ]
    assert errors == []


def test_parse_lines_multi_line_shopping():
    arg = "@an Mua ức gà | 400g ức gà\nTrứng gà"
    tasks, errors = parse_lines(arg, "shopping")
    assert tasks[0].content == "Mua ức gà"
    assert tasks[0].assignee == "an"
    assert tasks[0].description == "400g ức gà"
    assert tasks[1].content == "Trứng gà"
    assert tasks[1].assignee is None
    assert tasks[1].description is None
    assert errors == []


def test_parse_lines_skips_blank_lines():
    arg = "@an Mua cà phê\n\n   \nDọn kho"
    tasks, errors = parse_lines(arg, "todo")
    assert len(tasks) == 2
    assert errors == []


def test_parse_lines_reports_error_with_line_number_when_multiple():
    arg = "@an Mua cà phê\n | 400g ức gà\n@minh Gọi khách hàng"
    tasks, errors = parse_lines(arg, "shopping")
    assert len(tasks) == 2  # dòng 1 và dòng 3 hợp lệ
    assert len(errors) == 1
    assert errors[0].startswith("Dòng 2:")


def test_parse_lines_single_line_error_has_no_line_prefix():
    tasks, errors = parse_lines(" | 400g ức gà", "shopping")
    assert tasks == []
    assert len(errors) == 1
    assert not errors[0].startswith("Dòng")


def test_parse_lines_all_lines_invalid():
    arg = " | mô tả 1\n | mô tả 2"
    tasks, errors = parse_lines(arg, "shopping")
    assert tasks == []
    assert len(errors) == 2
