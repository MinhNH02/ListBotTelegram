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
