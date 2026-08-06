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
| `/shopping @an Mua ức gà \| 400g ức gà` | Thêm món mua sắm (mô tả tùy chọn) |
| `/clear` | Xóa các mục đã xong |

Chỉ người được giao (@username) mới tick được việc của mình; việc chung thì người tạo tick.
Muốn được giao việc, bạn cần đặt @username trong cài đặt Telegram.

### Thêm nhiều việc cùng lúc

Xuống dòng sau lệnh, mỗi dòng là một việc:

```
/list
@an Mua cà phê
@minh Gọi khách hàng
Dọn kho
```

Áp dụng cho cả `/list` và `/shopping`. Dòng nào lỗi cú pháp sẽ được báo riêng, các dòng đúng vẫn được thêm bình thường.
