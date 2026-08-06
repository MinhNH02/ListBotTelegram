import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
    description = task["description"]
    detail = f" — {html.escape(description)}" if description else ""
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

    buttons = [
        [InlineKeyboardButton(f"✅ {_short(t['content'])}", callback_data=f"done:{t['id']}")]
        for t in pending
    ]
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None
    return "\n".join(lines), keyboard
