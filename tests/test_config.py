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
