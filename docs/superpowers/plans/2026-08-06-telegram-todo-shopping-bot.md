# Telegram To-do & Shopping Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây bot Telegram dùng trong group để giao việc (`/list`) và lập danh sách mua sắm có đơn giá (`/shopping`), với nút ✅ tick done phân quyền theo người được giao.

**Architecture:** Python async bot (`python-telegram-bot` v20+) chạy long-polling trên PC. Logic thuần (parsing, kiểm tra quyền, render, DB) tách thành các module nhỏ, thuần túy, kiểm thử bằng pytest. Handlers Telegram là lớp mỏng gọi các module đó. Dữ liệu lưu SQLite cục bộ.

**Tech Stack:** Python 3.10+, python-telegram-bot (v20+, async), SQLite (`sqlite3`), python-dotenv, pytest.

## Global Constraints

- Python 3.10+ (dùng cú pháp `str | None`).
- `python-telegram-bot>=20.0` — API **async**; mọi handler là `async def`.
- Toàn bộ chữ hiển thị cho người dùng bằng **tiếng Việt**.
- Định dạng tin nhắn dùng `parse_mode=ParseMode.HTML`; nội dung người dùng phải `html.escape` trước khi chèn.
- Gạch ngang dùng thẻ `<s>...</s>`.
- Callback data dạng `done:{task_id}`.
- Token đọc từ biến môi trường `TELEGRAM_TOKEN` (file `.env`); **không bao giờ commit `.env`**.
- Danh sách khai báo trong `config.LISTS`; thêm danh sách mới = thêm 1 entry, không sửa logic.
- Tiền tệ VND: số nguyên, phân tách hàng nghìn bằng dấu `.`, hậu tố `đ` (vd `25.000đ`).
- Tất cả file mã nguồn đặt ở thư mục gốc repo; test đặt trong `tests/`.

---

## File Structure

- `config.py` — nạp `.env`, khai báo `TOKEN` và `LISTS`.
- `parsing.py` — hàm thuần: tách assignee, parse todo, parse shopping, lấy phần đối số của lệnh.
- `permissions.py` — hàm thuần `can_tick(...)`.
- `db.py` — khởi tạo & truy vấn SQLite.
- `render.py` — dựng text + inline keyboard; định dạng tiền.
- `handlers.py` — các async handler Telegram + hàm đăng ký handler.
- `bot.py` — điểm khởi động.
- `tests/` — `test_parsing.py`, `test_permissions.py`, `test_db.py`, `test_render.py`.
- `.env.example`, `.gitignore`, `requirements.txt`, `README.md`.

---

## Task 1: Scaffold dự án & cấu hình

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `config.TOKEN: str`, `config.LISTS: dict[str, dict]`. Mỗi entry: `{"command": str, "title": str, "kind": "todo"|"shopping"}`.

- [ ] **Step 1: Tạo `requirements.txt`**

```
python-telegram-bot>=20.0
python-dotenv>=1.0
pytest>=7.0
```

- [ ] **Step 2: Tạo `.gitignore`**

```
.env
bot.db
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Tạo `.env.example`**

```
TELEGRAM_TOKEN=dan-token-tu-BotFather-vao-day
```

- [ ] **Step 4: Cài dependencies**

Run: `pip install -r requirements.txt`
Expected: cài thành công python-telegram-bot, python-dotenv, pytest.

- [ ] **Step 5: Viết test cấu hình (failing)**

`tests/test_config.py`:
```python
import config


def test_lists_have_todo_and_shopping():
    assert "todo" in config.LISTS
    assert "shopping" in config.LISTS


def test_todo_config_shape():
    todo = config.LISTS["todo"]
    assert todo["command"] == "list"
    assert todo["kind"] == "todo"
    assert isinstance(todo["title"], str)


def test_shopping_is_shopping_kind():
    assert config.LISTS["shopping"]["command"] == "shopping"
    assert config.LISTS["shopping"]["kind"] == "shopping"
```

- [ ] **Step 6: Chạy test để xác nhận fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`.

- [ ] **Step 7: Viết `config.py`**

```python
import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Khai báo các danh sách. Thêm danh sách mới = thêm 1 entry ở đây.
# kind: "todo"  -> chỉ nội dung việc
#       "shopping" -> tên | số lượng | đơn giá, có tính tổng tiền
LISTS = {
    "todo": {
        "command": "list",
        "title": "📋 Công việc cần làm",
        "kind": "todo",
    },
    "shopping": {
        "command": "shopping",
        "title": "🛒 Mua sắm",
        "kind": "shopping",
    },
}
```

- [ ] **Step 8: Chạy test để xác nhận pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 passed).

- [ ] **Step 9: Commit**

```bash
git add requirements.txt .gitignore .env.example config.py tests/test_config.py
git commit -m "feat: scaffold dự án và cấu hình danh sách"
```

---

## Task 2: Module parsing (`parsing.py`)

**Files:**
- Create: `parsing.py`
- Test: `tests/test_parsing.py`

**Interfaces:**
- Produces:
  - `@dataclass ParsedTask` với các trường: `content: str`, `assignee: str | None = None`, `quantity: float | None = None`, `unit_price: float | None = None`.
  - `extract_assignee(arg: str) -> tuple[str | None, str]` — nếu `arg` bắt đầu bằng `@`, trả `(username_không_@, phần_còn_lại)`; ngược lại `(None, arg)`.
  - `parse_todo(arg: str) -> ParsedTask` — raise `ValueError` nếu nội dung rỗng.
  - `parse_shopping(arg: str) -> ParsedTask` — tách phần còn lại theo `|` thành `[tên, số lượng?, đơn giá?]`; số lượng/đơn giá tùy chọn; raise `ValueError` nếu tên rỗng hoặc số không hợp lệ.
  - `get_arg_text(message_text: str) -> str` — bỏ token lệnh đầu tiên, trả phần đối số đã strip (rỗng nếu không có).

- [ ] **Step 1: Viết test (failing)**

`tests/test_parsing.py`:
```python
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
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/test_parsing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'parsing'`.

- [ ] **Step 3: Viết `parsing.py`**

```python
from dataclasses import dataclass


@dataclass
class ParsedTask:
    content: str
    assignee: str | None = None
    quantity: float | None = None
    unit_price: float | None = None


def extract_assignee(arg: str) -> tuple[str | None, str]:
    arg = arg.strip()
    if arg.startswith("@"):
        parts = arg.split(maxsplit=1)
        assignee = parts[0][1:]
        rest = parts[1].strip() if len(parts) > 1 else ""
        return assignee, rest
    return None, arg


def parse_todo(arg: str) -> ParsedTask:
    assignee, rest = extract_assignee(arg)
    content = rest.strip()
    if not content:
        raise ValueError("Nội dung việc không được để trống.")
    return ParsedTask(content=content, assignee=assignee)


def _parse_number(text: str, label: str) -> float:
    cleaned = text.replace(".", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"{label} phải là số.")


def parse_shopping(arg: str) -> ParsedTask:
    assignee, rest = extract_assignee(arg)
    parts = [p.strip() for p in rest.split("|")]
    name = parts[0] if parts else ""
    if not name:
        raise ValueError("Tên hàng không được để trống.")
    quantity = None
    unit_price = None
    if len(parts) >= 2 and parts[1]:
        quantity = _parse_number(parts[1], "Số lượng")
    if len(parts) >= 3 and parts[2]:
        unit_price = _parse_number(parts[2], "Đơn giá")
    return ParsedTask(
        content=name, assignee=assignee, quantity=quantity, unit_price=unit_price
    )


def get_arg_text(message_text: str) -> str:
    parts = message_text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""
```

- [ ] **Step 4: Chạy test để xác nhận pass**

Run: `pytest tests/test_parsing.py -v`
Expected: PASS (tất cả).

- [ ] **Step 5: Commit**

```bash
git add parsing.py tests/test_parsing.py
git commit -m "feat: parsing lệnh todo và shopping"
```

---

## Task 3: Kiểm tra quyền tick (`permissions.py`)

**Files:**
- Create: `permissions.py`
- Test: `tests/test_permissions.py`

**Interfaces:**
- Consumes: một `task` là mapping có khóa `assignee` (str | None) và `creator_id` (int).
- Produces: `can_tick(task, user_id: int, username: str | None) -> tuple[bool, str]` — trả `(True, "")` nếu được phép; `(False, lý_do)` nếu không. So khớp username không phân biệt hoa thường.

- [ ] **Step 1: Viết test (failing)**

`tests/test_permissions.py`:
```python
from permissions import can_tick


def test_assigned_user_can_tick():
    task = {"assignee": "an", "creator_id": 111}
    ok, reason = can_tick(task, user_id=999, username="An")
    assert ok is True
    assert reason == ""


def test_other_user_cannot_tick_assigned():
    task = {"assignee": "an", "creator_id": 111}
    ok, reason = can_tick(task, user_id=999, username="minh")
    assert ok is False
    assert "an" in reason


def test_creator_can_tick_unassigned():
    task = {"assignee": None, "creator_id": 111}
    ok, reason = can_tick(task, user_id=111, username="minh")
    assert ok is True


def test_non_creator_cannot_tick_unassigned():
    task = {"assignee": None, "creator_id": 111}
    ok, reason = can_tick(task, user_id=222, username="an")
    assert ok is False


def test_assigned_but_ticker_has_no_username():
    task = {"assignee": "an", "creator_id": 111}
    ok, reason = can_tick(task, user_id=999, username=None)
    assert ok is False
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/test_permissions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'permissions'`.

- [ ] **Step 3: Viết `permissions.py`**

```python
def can_tick(task, user_id: int, username: str | None) -> tuple[bool, str]:
    assignee = task["assignee"]
    if assignee:
        if username and username.lower() == assignee.lower():
            return True, ""
        return False, f"Chỉ @{assignee} mới tick được việc này."
    if user_id == task["creator_id"]:
        return True, ""
    return False, "Chỉ người tạo mới tick được việc này."
```

- [ ] **Step 4: Chạy test để xác nhận pass**

Run: `pytest tests/test_permissions.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add permissions.py tests/test_permissions.py
git commit -m "feat: kiểm tra quyền tick done"
```

---

## Task 4: Lưu trữ SQLite (`db.py`)

**Files:**
- Create: `db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces (module dùng biến `DB_PATH: str`, mặc định `"bot.db"`; test gán lại trước khi gọi `init_db`):
  - `init_db() -> None` — tạo bảng `tasks` nếu chưa có.
  - `add_task(chat_id: int, list_key: str, content: str, quantity: float | None, unit_price: float | None, assignee: str | None, creator_id: int, creator_name: str) -> int` — trả `id` mới.
  - `get_tasks(chat_id: int, list_key: str) -> list[sqlite3.Row]` — mọi task của (chat, list), sắp theo `id` tăng dần.
  - `get_task(task_id: int) -> sqlite3.Row | None`.
  - `mark_done(task_id: int, done_by: str) -> None` — set `status='done'`, ghi `done_at`, `done_by`.
  - `clear_done(chat_id: int) -> int` — xóa mọi task `status='done'` của chat, trả số dòng đã xóa.
  - Row có các khóa: `id, chat_id, list_key, content, quantity, unit_price, assignee, creator_id, creator_name, status, created_at, done_at, done_by`.

- [ ] **Step 1: Viết test (failing)**

`tests/test_db.py`:
```python
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
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'db'`.

- [ ] **Step 3: Viết `db.py`**

```python
import sqlite3
from datetime import datetime, timezone

DB_PATH = "bot.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                list_key TEXT NOT NULL,
                content TEXT NOT NULL,
                quantity REAL,
                unit_price REAL,
                assignee TEXT,
                creator_id INTEGER NOT NULL,
                creator_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                done_at TEXT,
                done_by TEXT
            )
            """
        )


def add_task(
    chat_id: int,
    list_key: str,
    content: str,
    quantity: float | None,
    unit_price: float | None,
    assignee: str | None,
    creator_id: int,
    creator_name: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks
                (chat_id, list_key, content, quantity, unit_price, assignee,
                 creator_id, creator_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                chat_id, list_key, content, quantity, unit_price, assignee,
                creator_id, creator_name, _now(),
            ),
        )
        return int(cur.lastrowid)


def get_tasks(chat_id: int, list_key: str) -> list[sqlite3.Row]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM tasks WHERE chat_id = ? AND list_key = ? ORDER BY id ASC",
            (chat_id, list_key),
        )
        return cur.fetchall()


def get_task(task_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cur.fetchone()


def mark_done(task_id: int, done_by: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done', done_at = ?, done_by = ? WHERE id = ?",
            (_now(), done_by, task_id),
        )


def clear_done(chat_id: int) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE chat_id = ? AND status = 'done'", (chat_id,)
        )
        return cur.rowcount
```

- [ ] **Step 4: Chạy test để xác nhận pass**

Run: `pytest tests/test_db.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: lưu trữ task bằng SQLite"
```

---

## Task 5: Render danh sách (`render.py`)

**Files:**
- Create: `render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: `list_cfg` (một entry của `config.LISTS`, có khóa `title`, `kind`); `tasks` là list các mapping có khóa `id, content, quantity, unit_price, assignee, status`.
- Produces:
  - `format_money(amount: float | None) -> str` — `None` → `""`; số → `"25.000đ"`.
  - `render_list(list_cfg: dict, tasks: list) -> tuple[str, InlineKeyboardMarkup | None]` — text HTML + keyboard (một nút mỗi task **pending**, callback `done:{id}`). Không có task → keyboard `None`. Với `kind == "shopping"`, thêm dòng tổng tiền các món **chưa mua** (có đủ quantity & unit_price).

- [ ] **Step 1: Viết test (failing)**

`tests/test_render.py`:
```python
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
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/test_render.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'render'`.

- [ ] **Step 3: Viết `render.py`**

```python
import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def format_money(amount: float | None) -> str:
    if amount is None:
        return ""
    return f"{int(round(amount)):,}".replace(",", ".") + "đ"


def _line_todo(task) -> str:
    mark = "✅" if task["status"] == "done" else "⬜"
    content = html.escape(task["content"])
    if task["status"] == "done":
        content = f"<s>{content}</s>"
    suffix = f" — @{html.escape(task['assignee'])}" if task["assignee"] else ""
    return f"{mark} {content}{suffix}"


def _line_shopping(task) -> str:
    mark = "✅" if task["status"] == "done" else "⬜"
    content = html.escape(task["content"])
    if task["status"] == "done":
        content = f"<s>{content}</s>"
    qty = task["quantity"]
    price = task["unit_price"]
    detail = ""
    if qty is not None and price is not None:
        total = format_money(qty * price)
        qty_str = f"{qty:g}"
        detail = f" — {qty_str} × {format_money(price)} = {total}"
    elif qty is not None:
        detail = f" — SL {qty:g}"
    suffix = f" — @{html.escape(task['assignee'])}" if task["assignee"] else ""
    return f"{mark} {content}{detail}{suffix}"


def _short(text: str, limit: int = 30) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_list(list_cfg: dict, tasks: list):
    kind = list_cfg["kind"]
    line_fn = _line_shopping if kind == "shopping" else _line_todo

    lines = [f"<b>{html.escape(list_cfg['title'])}</b>", ""]
    if not tasks:
        lines.append("(Chưa có mục nào. Thêm bằng cách gõ lệnh kèm nội dung.)")
        return "\n".join(lines), None

    for task in tasks:
        lines.append(line_fn(task))

    pending = [t for t in tasks if t["status"] != "done"]

    if kind == "shopping":
        total = sum(
            (t["quantity"] * t["unit_price"])
            for t in pending
            if t["quantity"] is not None and t["unit_price"] is not None
        )
        lines.append("")
        lines.append(f"💰 Tổng cộng (chưa mua): {format_money(total)}")

    buttons = [
        [InlineKeyboardButton(f"✅ {_short(t['content'])}", callback_data=f"done:{t['id']}")]
        for t in pending
    ]
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None
    return "\n".join(lines), keyboard
```

- [ ] **Step 4: Chạy test để xác nhận pass**

Run: `pytest tests/test_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "feat: render danh sách và nút tick"
```

---

## Task 6: Handlers Telegram (`handlers.py`)

**Files:**
- Create: `handlers.py`
- (Không có unit test tự động — handlers là lớp mỏng gọi các module đã kiểm thử; xác minh bằng test thủ công ở Task 7.)

**Interfaces:**
- Consumes: `config.LISTS`, `parsing.*`, `permissions.can_tick`, `db.*`, `render.render_list`.
- Produces: `register(app) -> None` — đăng ký toàn bộ handler vào `Application`.

- [ ] **Step 1: Viết `handlers.py`**

```python
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
import db
from parsing import get_arg_text, parse_shopping, parse_todo
from permissions import can_tick
from render import render_list

HELP_TEXT = (
    "<b>Bot Công việc & Mua sắm</b>\n\n"
    "📋 <b>Công việc</b>\n"
    "• <code>/list</code> — xem danh sách việc\n"
    "• <code>/list @an Nội dung việc</code> — thêm việc (bỏ @an = việc chung)\n\n"
    "🛒 <b>Mua sắm</b>\n"
    "• <code>/shopping</code> — xem danh sách mua sắm\n"
    "• <code>/shopping @an Tên hàng | số lượng | đơn giá</code> — thêm món\n"
    "  (số lượng và đơn giá có thể bỏ trống)\n\n"
    "✅ Bấm nút để đánh dấu xong. Chỉ người được giao (@username) mới tick "
    "được; việc chung thì người tạo tick.\n"
    "🧹 <code>/clear</code> — xóa các mục đã xong.\n\n"
    "Lưu ý: để được giao việc, bạn cần đặt @username trong Telegram."
)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def _show_list(update: Update, list_key: str) -> None:
    chat_id = update.effective_chat.id
    tasks = db.get_tasks(chat_id, list_key)
    text, keyboard = render_list(config.LISTS[list_key], tasks)
    await update.message.reply_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.HTML
    )


def _make_list_handler(list_key: str):
    kind = config.LISTS[list_key]["kind"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        arg = get_arg_text(update.message.text)
        if not arg:
            await _show_list(update, list_key)
            return
        try:
            parsed = parse_shopping(arg) if kind == "shopping" else parse_todo(arg)
        except ValueError as err:
            await update.message.reply_text(f"⚠️ {err}")
            return
        user = update.effective_user
        db.add_task(
            chat_id=update.effective_chat.id,
            list_key=list_key,
            content=parsed.content,
            quantity=parsed.quantity,
            unit_price=parsed.unit_price,
            assignee=parsed.assignee,
            creator_id=user.id,
            creator_name=user.username or user.full_name,
        )
        await _show_list(update, list_key)

    return handler


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    removed = db.clear_done(update.effective_chat.id)
    await update.message.reply_text(f"🧹 Đã xóa {removed} mục đã xong.")


async def on_tick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    task_id = int(query.data.split(":")[1])
    task = db.get_task(task_id)
    if task is None:
        await query.answer("Mục không còn tồn tại.", show_alert=True)
        return
    if task["status"] == "done":
        await query.answer("Mục này đã xong rồi.")
        return

    user = query.from_user
    ok, reason = can_tick(task, user.id, user.username)
    if not ok:
        await query.answer(reason, show_alert=True)
        return

    db.mark_done(task_id, done_by=user.username or user.full_name)
    await query.answer("Đã đánh dấu xong ✅")

    tasks = db.get_tasks(task["chat_id"], task["list_key"])
    text, keyboard = render_list(config.LISTS[task["list_key"]], tasks)
    await query.edit_message_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.HTML
    )


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    for list_key, cfg in config.LISTS.items():
        app.add_handler(CommandHandler(cfg["command"], _make_list_handler(list_key)))
    app.add_handler(CallbackQueryHandler(on_tick, pattern=r"^done:\d+$"))
```

- [ ] **Step 2: Kiểm tra import không lỗi**

Run: `python -c "import handlers"`
Expected: không lỗi (thoát im lặng). Nếu lỗi import → sửa trước khi đi tiếp.

- [ ] **Step 3: Commit**

```bash
git add handlers.py
git commit -m "feat: handlers Telegram cho lệnh và nút tick"
```

---

## Task 7: Điểm khởi động, README & test thủ công

**Files:**
- Create: `bot.py`, `README.md`

**Interfaces:**
- Consumes: `config.TOKEN`, `db.init_db`, `handlers.register`.

- [ ] **Step 1: Viết `bot.py`**

```python
from telegram import Update
from telegram.ext import Application

import config
import db
import handlers


def main() -> None:
    if not config.TOKEN:
        raise SystemExit(
            "Chưa có TELEGRAM_TOKEN. Tạo file .env từ .env.example và dán token."
        )
    db.init_db()
    app = Application.builder().token(config.TOKEN).build()
    handlers.register(app)
    print("Bot đang chạy... Nhấn Ctrl+C để dừng.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Viết `README.md`**

````markdown
# Bot Telegram — Công việc & Mua sắm

Bot dùng trong group Telegram để giao việc và lập danh sách mua sắm, có nút tick done.

## Cài đặt

1. Cài Python 3.10+.
2. Tạo bot: nhắn **@BotFather** → `/newbot` → làm theo hướng dẫn → nhận **token**.
3. Trong @BotFather: `/setprivacy` → chọn bot → **Disable** (để bot đọc lệnh trong group).
4. Cài thư viện:
   ```
   pip install -r requirements.txt
   ```
5. Tạo file `.env` (copy từ `.env.example`) và dán token:
   ```
   TELEGRAM_TOKEN=123456:ABC-token-that-cua-ban
   ```

## Chạy

```
python bot.py
```

Sau đó thêm bot vào group và gõ `/help`.

## Lệnh

| Lệnh | Tác dụng |
|------|----------|
| `/help` | Hướng dẫn |
| `/list` | Xem việc cần làm |
| `/list @an Mua cà phê` | Thêm việc, giao cho @an |
| `/shopping` | Xem danh sách mua sắm |
| `/shopping @an Sữa tươi \| 2 \| 25000` | Thêm món mua sắm |
| `/clear` | Xóa các mục đã xong |

Chỉ người được giao (@username) mới tick được việc của mình; việc chung thì người tạo tick.
Muốn được giao việc, bạn cần đặt @username trong cài đặt Telegram.
````

- [ ] **Step 3: Chạy toàn bộ test tự động**

Run: `pytest -v`
Expected: tất cả test (config, parsing, permissions, db, render) PASS.

- [ ] **Step 4: Test thủ công end-to-end trên Telegram**

Điều kiện: đã có token trong `.env`, đã disable privacy, đã thêm bot vào một group thử nghiệm (có ít nhất 2 tài khoản có @username).

Chạy `python bot.py`, rồi trong group kiểm tra lần lượt:
1. `/help` → hiện hướng dẫn.
2. `/list` → "(Chưa có mục nào...)".
3. `/list @<username_ban> Gọi khách hàng` → hiện danh sách có 1 việc + 1 nút ✅.
4. `/list Dọn kho` (không tag) → danh sách 2 việc.
5. Bấm nút ✅ "Gọi khách hàng" bằng tài khoản **khác** (không phải người được giao) → hiện alert "Chỉ @... mới tick được".
6. Bấm nút ✅ "Gọi khách hàng" bằng đúng tài khoản được giao → việc bị gạch ngang, nút biến mất.
7. `/shopping @<username_ban> Sữa tươi | 2 | 25000` → hiện món + "50.000đ" + "Tổng cộng".
8. `/shopping Trứng | 10 | 3000` → tổng cập nhật "80.000đ".
9. `/shopping Muối` (không SL/giá) → thêm được, không có dòng giá.
10. Tick một món shopping → gạch ngang, tổng giảm tương ứng.
11. `/clear` → báo số mục đã xóa; gõ lại `/list` và `/shopping` thấy các mục đã xong biến mất.
12. Dừng bot (Ctrl+C), chạy lại `python bot.py`, gõ `/list` → dữ liệu vẫn còn (đã lưu SQLite).

Nếu có bước sai → dùng superpowers:systematic-debugging để xử lý trước khi hoàn tất.

- [ ] **Step 5: Commit**

```bash
git add bot.py README.md
git commit -m "feat: điểm khởi động bot và tài liệu README"
```

---

## Self-Review Notes

- **Spec coverage:** `/list`, `/shopping` (thêm/xem) → Task 6; số lượng/đơn giá + tổng tiền → Task 5; tag @username + phân quyền tick → Task 3 & 6; gạch ngang khi xong → Task 5; `/clear` → Task 4 & 6; SQLite bền vững → Task 4 & Task 7 (bước 12); cấu hình danh sách mở rộng → Task 1; hướng dẫn cài đặt → Task 7. Đủ.
- **Placeholder scan:** không có TODO/TBD; mọi bước có code cụ thể.
- **Type consistency:** `ParsedTask` (content/assignee/quantity/unit_price) khớp giữa Task 2 và Task 6; khóa Row của `db` khớp với `render` và `permissions`; `render_list(list_cfg, tasks)` chữ ký nhất quán Task 5 ↔ Task 6.
```
