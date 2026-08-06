from dataclasses import dataclass


@dataclass
class ParsedTask:
    content: str
    assignee: str | None = None
    description: str | None = None


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


def parse_shopping(arg: str) -> ParsedTask:
    assignee, rest = extract_assignee(arg)
    parts = rest.split("|", maxsplit=1)
    name = parts[0].strip()
    if not name:
        raise ValueError("Tên hàng không được để trống.")
    description = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    return ParsedTask(content=name, assignee=assignee, description=description)


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
