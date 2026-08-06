import pytest

import db as db_module


@pytest.fixture
def db(tmp_path):
    db_module.DB_PATH = str(tmp_path / "test.db")
    db_module.init_db()
    return db_module


def test_add_and_get_task(db):
    task_id = db.add_task(
        chat_id=1, list_key="todo", content="Dọn kho",
        quantity=None, unit_price=None, assignee="an",
        creator_id=111, creator_name="Minh",
    )
    tasks = db.get_tasks(chat_id=1, list_key="todo")
    assert len(tasks) == 1
    row = tasks[0]
    assert row["id"] == task_id
    assert row["content"] == "Dọn kho"
    assert row["assignee"] == "an"
    assert row["status"] == "pending"


def test_tasks_are_scoped_by_chat_and_list(db):
    db.add_task(1, "todo", "A", None, None, None, 111, "M")
    db.add_task(2, "todo", "B", None, None, None, 111, "M")
    db.add_task(1, "shopping", "C", 1, 1000, None, 111, "M")
    assert len(db.get_tasks(1, "todo")) == 1
    assert len(db.get_tasks(2, "todo")) == 1
    assert len(db.get_tasks(1, "shopping")) == 1


def test_mark_done(db):
    tid = db.add_task(1, "todo", "X", None, None, None, 111, "M")
    db.mark_done(tid, done_by="an")
    row = db.get_task(tid)
    assert row["status"] == "done"
    assert row["done_by"] == "an"
    assert row["done_at"] is not None


def test_clear_done_only_removes_done(db):
    t1 = db.add_task(1, "todo", "X", None, None, None, 111, "M")
    db.add_task(1, "todo", "Y", None, None, None, 111, "M")
    db.mark_done(t1, "an")
    removed = db.clear_done(chat_id=1)
    assert removed == 1
    remaining = db.get_tasks(1, "todo")
    assert len(remaining) == 1
    assert remaining[0]["content"] == "Y"


def test_get_task_missing_returns_none(db):
    assert db.get_task(999) is None
