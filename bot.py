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
