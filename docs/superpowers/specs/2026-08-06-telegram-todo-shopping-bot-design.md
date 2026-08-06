# Thiết kế: Telegram Bot Quản lý Công việc & Mua sắm (Group)

**Ngày:** 2026-08-06
**Trạng thái:** Đã duyệt thiết kế, chờ review spec

## 1. Mục tiêu

Một bot Telegram dùng trong **group chat**, giúp các thành viên:
- Giao việc cho nhau (danh sách công việc cần làm).
- Lập danh sách mua sắm có số lượng, đơn giá, tính tổng tiền.
- Đánh dấu hoàn thành (tick ✅) từng mục.

Bot chạy trên **PC Windows** của người dùng (long-polling), dữ liệu lưu cục bộ.

## 2. Phạm vi & Quyết định đã chốt

- **Đối tượng:** nhiều người trong 1 group chat; mỗi group có danh sách riêng.
- **Quyền giao việc:** ai trong group cũng giao được.
- **Chỉ định người nhận:** tag `@username`; bỏ trống = việc/món chung.
- **Danh sách:** bắt đầu với 2 loại cố định — `/list` (công việc) và `/shopping` (mua sắm); thiết kế cho phép thêm loại mới bằng cấu hình.
- **Vòng đời việc:** giữ đến khi tick xong (không reset theo ngày).
- **Quyền tick:** chỉ `@username` được giao mới tick được; việc/món chung thì chỉ người tạo tick được.
- **Hiển thị khi xong:** gạch ngang + ✓, vẫn hiện; nút ✅ của mục đó biến mất.
- **`/clear`:** xóa các mục đã xong để danh sách gọn.
- **Vận hành:** chạy cục bộ trên PC; code viết sẵn để sau này deploy cloud dễ dàng.

## 3. Công nghệ

- **Ngôn ngữ:** Python 3.10+
- **Thư viện bot:** `python-telegram-bot` (v20+, async)
- **Lưu trữ:** SQLite (module `sqlite3` chuẩn) — 1 file `bot.db`, bền vững qua restart.
- **Cấu hình:** `python-dotenv` để đọc token từ `.env`.

*Đã cân nhắc & loại:* Node.js/Telegraf (tương đương nhưng người dùng chọn Python); lưu JSON (dễ hỏng khi nhiều thao tác đồng thời).

## 4. Lệnh (Commands)

| Lệnh | Tác dụng |
|------|----------|
| `/start`, `/help` | Hướng dẫn sử dụng |
| `/list` | Hiện danh sách công việc chưa xong (kèm nút ✅) |
| `/list [@user] <nội dung>` | Thêm việc; `@user` tùy chọn |
| `/shopping` | Hiện danh sách mua sắm + tổng tiền |
| `/shopping [@user] <tên> \| <số lượng> \| <đơn giá>` | Thêm món; số lượng/đơn giá tùy chọn |
| `/clear` | (dùng trong ngữ cảnh 1 danh sách) xóa các mục đã xong |

### Quy tắc phân tích lệnh (parsing)

- Nếu token đầu tiên bắt đầu bằng `@` → đó là **assignee** (lưu username không kèm `@`), phần còn lại là nội dung.
- **`/list`:** phần còn lại là nội dung việc.
- **`/shopping`:** phần còn lại tách theo dấu `|` thành `[tên, số lượng, đơn giá]`.
  - Chỉ có tên → thêm món không có giá.
  - Có số lượng + đơn giá → tính `thành tiền = số lượng × đơn giá`.
  - Số lượng/đơn giá không phải số hợp lệ → báo lỗi hướng dẫn cú pháp.

### `/clear` áp cho danh sách nào?

Vì `/clear` không nêu rõ danh sách, bot xóa mục đã xong của **cả hai** danh sách trong group đó, và báo số mục đã xóa. (Đơn giản, tránh mơ hồ.)

## 5. Hiển thị (Rendering)

Mỗi lần `/list` hoặc `/shopping`, bot gửi 1 tin nhắn gồm:
- **Phần chữ:** liệt kê tất cả mục. Mục chưa xong: `⬜`. Mục đã xong: `✅ ~~gạch ngang~~`.
- **Nút bấm (inline keyboard):** mỗi mục **chưa xong** một nút `✅ <nội dung rút gọn>`. Mục đã xong không có nút.

### Ví dụ — công việc
```
📋 Công việc cần làm

✅ ~~Mua cà phê~~ — @an
⬜ Gọi khách hàng — @minh
⬜ Dọn kho

[ ✅ Gọi khách hàng ]
[ ✅ Dọn kho ]
```

### Ví dụ — mua sắm
```
🛒 Mua sắm

⬜ Sữa tươi — 2 × 25.000 = 50.000đ — @an
⬜ Trứng gà — 10 × 3.000 = 30.000đ
✅ ~~Bánh mì~~ — 5 × 10.000 = 50.000đ

💰 Tổng cộng (chưa mua): 80.000đ

[ ✅ Sữa tươi ]
[ ✅ Trứng gà ]
```

- Số tiền định dạng có dấu chấm phân tách hàng nghìn, hậu tố `đ`.
- Tổng cộng tính trên các món **chưa mua** (có thể ghi thêm tổng cả danh sách nếu cần — quyết định khi implement, mặc định: tổng chưa mua).

## 6. Luồng tick done

1. Người dùng bấm nút `✅` → Telegram gửi callback query chứa `task_id`.
2. Bot đọc task từ DB, xác định người bấm (`from_user`).
3. **Kiểm tra quyền:**
   - Nếu task có `assignee`: chỉ cho phép khi `from_user.username == assignee`.
   - Nếu không có assignee (việc chung): chỉ cho phép khi `from_user.id == creator_id`.
   - Không đủ quyền → trả lời callback dạng alert riêng: "Chỉ @X mới tick được việc này" (không gửi tin ra nhóm).
4. Đủ quyền → cập nhật `status='done'`, ghi `done_at`, `done_by`.
5. Dựng lại tin nhắn (edit message) với trạng thái mới.

*Ghi chú:* việc đã xong giữ nguyên (không hỗ trợ undo ở bản đầu — YAGNI). Muốn dọn thì dùng `/clear`.

## 7. Mô hình dữ liệu (SQLite)

Bảng `tasks`:

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `chat_id` | INTEGER | ID group; phân tách danh sách theo group |
| `list_key` | TEXT | `'todo'` hoặc `'shopping'` |
| `content` | TEXT | nội dung việc / tên hàng |
| `quantity` | REAL NULL | chỉ shopping |
| `unit_price` | REAL NULL | chỉ shopping |
| `assignee` | TEXT NULL | username không kèm `@` |
| `creator_id` | INTEGER | user id người tạo |
| `creator_name` | TEXT | tên/username người tạo (hiển thị) |
| `status` | TEXT | `'pending'` \| `'done'` |
| `created_at` | TEXT | ISO timestamp |
| `done_at` | TEXT NULL | |
| `done_by` | TEXT NULL | username/tên người tick |

## 8. Cấu trúc code (mỗi file một nhiệm vụ)

- **`config.py`** — đọc token từ `.env`; khai báo `LISTS` (dict cấu hình từng danh sách: key, command, tiêu đề, emoji, có phải loại shopping không). Thêm danh sách mới = thêm 1 entry.
- **`db.py`** — khởi tạo DB & các hàm: `init_db()`, `add_task(...)`, `get_tasks(chat_id, list_key)`, `get_task(task_id)`, `mark_done(task_id, user)`, `clear_done(chat_id)`.
- **`render.py`** — `render_list(list_key, tasks) -> (text, InlineKeyboardMarkup)`; hàm định dạng tiền.
- **`handlers.py`** — các handler: `cmd_help`, `cmd_show_or_add` (dùng chung cho các danh sách), `cmd_clear`, `on_tick` (callback). Chứa logic parsing & kiểm tra quyền.
- **`bot.py`** — điểm khởi động: nạp config, đăng ký handler theo `LISTS`, chạy `run_polling()`.
- **`.env`** — `TELEGRAM_TOKEN=...` (không commit; có `.env.example`).
- **`requirements.txt`** — `python-telegram-bot`, `python-dotenv`.
- **`README.md`** — hướng dẫn cài đặt & chạy.

## 9. Thiết lập & chạy (cho người dùng)

1. Cài Python 3.10+.
2. Tạo bot qua **@BotFather** → lấy token; đặt vào `.env`.
3. Trong @BotFather: **/setprivacy → Disable** để bot đọc được lệnh trong group.
4. `pip install -r requirements.txt`
5. `python bot.py`
6. Thêm bot vào group Telegram, thử `/help`.

## 10. Xử lý lỗi & trường hợp biên

- Sai cú pháp shopping (số lượng/đơn giá không phải số) → tin nhắn hướng dẫn cú pháp.
- `/list` hoặc `/shopping` khi danh sách rỗng → thông báo "Chưa có mục nào. Thêm bằng: ...".
- Người được giao **chưa đặt @username** → không tick được (giới hạn đã biết của phương án tag username); `/help` nêu rõ cần đặt username.
- Bot dùng trong **chat riêng** (không phải group) → vẫn hoạt động bình thường (chat_id cá nhân là một "danh sách" riêng).
- Callback từ task đã bị xóa (`/clear`) → trả lời "Mục không còn tồn tại".

## 11. Ngoài phạm vi (bản đầu)

- Nhắc hẹn theo giờ / thông báo tự động.
- Sửa nội dung mục sau khi tạo.
- Undo tick.
- Deploy cloud 24/7 (code viết sẵn để dễ chuyển sau).
- Phân quyền admin.
