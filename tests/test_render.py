from render import render_list


def test_render_empty_list():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    text, keyboard = render_list(cfg, [])
    assert "📋 Công việc cần làm" in text
    assert keyboard is None


def test_render_todo_pending_has_button():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 1, "content": "Gọi khách", "description": None,
         "assignee": "minh", "status": "pending"},
    ]
    text, keyboard = render_list(cfg, tasks)
    assert "Gọi khách" in text
    assert "@minh" in text
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1


def test_render_done_task_struck_no_button():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 1, "content": "Xong rồi", "description": None,
         "assignee": None, "status": "done"},
    ]
    text, keyboard = render_list(cfg, tasks)
    assert "<s>" in text
    assert keyboard is None  # không có task pending


def test_render_shopping_shows_description():
    cfg = {"title": "🛒 Mua sắm", "kind": "shopping"}
    tasks = [
        {"id": 1, "content": "Mua ức gà", "description": "400g ức gà",
         "assignee": "minh", "status": "pending"},
        {"id": 2, "content": "Trứng gà", "description": None,
         "assignee": None, "status": "done"},
    ]
    text, keyboard = render_list(cfg, tasks)
    assert "Mua ức gà" in text
    assert "400g ức gà" in text
    assert "@minh" in text
    assert "Trứng gà" in text
    assert len(keyboard.inline_keyboard) == 1  # chỉ Mua ức gà còn nút (chưa xong)


def test_render_shopping_no_description_omits_dash():
    cfg = {"title": "🛒 Mua sắm", "kind": "shopping"}
    tasks = [
        {"id": 1, "content": "Muối", "description": None,
         "assignee": None, "status": "pending"},
    ]
    text, _ = render_list(cfg, tasks)
    assert "Muối" in text


def test_render_button_callback_data_format():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 7, "content": "Việc A", "description": None,
         "assignee": None, "status": "pending"},
    ]
    _, keyboard = render_list(cfg, tasks)
    button = keyboard.inline_keyboard[0][0]
    assert button.callback_data == "done:7"


def test_render_escapes_html_in_message_text():
    cfg = {"title": "📋 Công việc cần làm", "kind": "todo"}
    tasks = [
        {"id": 1, "content": "A & <B>", "description": None,
         "assignee": None, "status": "pending"},
    ]
    text, _ = render_list(cfg, tasks)
    assert "A &amp; &lt;B&gt;" in text


def test_render_escapes_html_in_shopping_description():
    cfg = {"title": "🛒 Mua sắm", "kind": "shopping"}
    tasks = [
        {"id": 1, "content": "X", "description": "A & <B>",
         "assignee": None, "status": "pending"},
    ]
    text, _ = render_list(cfg, tasks)
    assert "A &amp; &lt;B&gt;" in text
