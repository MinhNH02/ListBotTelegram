def can_tick(task, user_id: int, username: str | None) -> tuple[bool, str]:
    assignee = task["assignee"]
    if assignee:
        if username and username.lower() == assignee.lower():
            return True, ""
        return False, f"Chỉ @{assignee} mới tick được việc này."
    if user_id == task["creator_id"]:
        return True, ""
    return False, "Chỉ người tạo mới tick được việc này."
