import math
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
    cleaned = text.strip().replace(".", "").replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        raise ValueError(f"{label} phải là số.")
    if not math.isfinite(value):
        raise ValueError(f"{label} phải là số.")
    return value


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


def parse_lines(arg: str, kind: str) -> tuple[list[ParsedTask], list[str]]:
    lines = [line.strip() for line in arg.split("\n")]
    lines = [line for line in lines if line]
    multi = len(lines) > 1
    parse_fn = parse_shopping if kind == "shopping" else parse_todo

    tasks: list[ParsedTask] = []
    errors: list[str] = []
    for i, line in enumerate(lines, start=1):
        try:
            tasks.append(parse_fn(line))
        except ValueError as err:
            prefix = f"Dòng {i}: " if multi else ""
            errors.append(f"{prefix}{err}")
    return tasks, errors
