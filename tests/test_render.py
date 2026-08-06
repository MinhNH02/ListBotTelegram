from render import format_money, render_list


def test_format_money():
    assert format_money(25000) == "25.000đ"
    assert format_money(50000) == "50.000đ"
    assert format_money(None) == ""


def test_render_empty_list():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    text, keyboard = render_list(cfg, [])
    assert "📋 Công việc cần làm" in text
    assert keyboard is None


def test_render_todo_pending_has_button():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 1, "content": "Gọi khách", "quantity": None,
         "unit_price": None, "assignee": "minh", "status": "pending"},
    ]
    text, keyboard = render_list(cfg, tasks)
    assert "Gọi khách" in text
    assert "@minh" in text
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1


def test_render_done_task_struck_no_button():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 1, "content": "Xong rồi", "quantity": None,
         "unit_price": None, "assignee": None, "status": "done"},
    ]
    text, keyboard = render_list(cfg, tasks)
    assert "<s>" in text
    assert keyboard is None  # không có task pending


def test_render_shopping_total_of_pending_only():
    cfg = {"title": "🛒 Mua sắm", "kind": "shopping"}
    tasks = [
        {"id": 1, "content": "Sữa", "quantity": 2, "unit_price": 25000,
         "assignee": None, "status": "pending"},
        {"id": 2, "content": "Bánh", "quantity": 5, "unit_price": 10000,
         "assignee": None, "status": "done"},
    ]
    text, keyboard = render_list(cfg, tasks)
    # chỉ Sữa (2 x 25.000 = 50.000) tính vào tổng, Bánh đã mua thì bỏ
    assert "50.000đ" in text
    assert "Tổng cộng" in text
    assert len(keyboard.inline_keyboard) == 1  # chỉ Sữa còn nút
