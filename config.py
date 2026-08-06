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
