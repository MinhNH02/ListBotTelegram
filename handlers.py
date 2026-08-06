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
from parsing import get_arg_text, parse_lines
from permissions import can_tick
from render import render_list

HELP_TEXT = (
    "<b>Bot Công việc & Mua sắm</b>\n\n"
    "📋 <b>Công việc</b>\n"
    "• <code>/list</code> — xem danh sách việc\n"
    "• <code>/list @an Nội dung việc</code> — thêm việc (bỏ @an = việc chung)\n"
    "• Thêm nhiều việc cùng lúc: xuống dòng, mỗi dòng 1 việc\n\n"
    "🛒 <b>Mua sắm</b>\n"
    "• <code>/shopping</code> — xem danh sách mua sắm\n"
    "• <code>/shopping @an Tên hàng | mô tả</code> — thêm món (mô tả tùy chọn)\n"
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
        tasks, errors = parse_lines(arg, kind)
        if not tasks:
            await update.message.reply_text("⚠️ " + "\n".join(errors))
            return
        user = update.effective_user
        for parsed in tasks:
            db.add_task(
                chat_id=update.effective_chat.id,
                list_key=list_key,
                content=parsed.content,
                description=parsed.description,
                assignee=parsed.assignee,
                creator_id=user.id,
                creator_name=user.username or user.full_name,
            )
        if errors:
            await update.message.reply_text(
                "⚠️ Một số dòng bị lỗi, các dòng còn lại đã được thêm:\n"
                + "\n".join(errors)
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
