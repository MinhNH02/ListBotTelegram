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
