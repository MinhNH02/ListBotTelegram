# Bot Telegram — Công việc & Mua sắm

Bot dùng trong group Telegram để giao việc và lập danh sách mua sắm, có nút tick done.

## Cài đặt

1. Cài Python 3.10+.
2. Tạo bot: nhắn **@BotFather** → `/newbot` → làm theo hướng dẫn → nhận **token**.
3. Trong @BotFather: `/setprivacy` → chọn bot → **Disable** (để bot đọc lệnh trong group).
4. Cài thư viện:
   ```
   pip install -r requirements.txt
   ```
5. Tạo file `.env` (copy từ `.env.example`) và dán token:
   ```
   TELEGRAM_TOKEN=123456:ABC-token-that-cua-ban
   ```

## Chạy

```
python bot.py
```

Sau đó thêm bot vào group và gõ `/help`.

## Lệnh

| Lệnh | Tác dụng |
|------|----------|
| `/help` | Hướng dẫn |
| `/list` | Xem việc cần làm |
| `/list @an Mua cà phê` | Thêm việc, giao cho @an |
| `/shopping` | Xem danh sách mua sắm |
| `/shopping @an Sữa tươi \| 2 \| 25000` | Thêm món mua sắm |
| `/clear` | Xóa các mục đã xong |

Chỉ người được giao (@username) mới tick được việc của mình; việc chung thì người tạo tick.
Muốn được giao việc, bạn cần đặt @username trong cài đặt Telegram.
