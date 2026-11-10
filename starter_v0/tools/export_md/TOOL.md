---
name: export_md
track: bonus
kind: action
provider: local
requires_env: []
inputs: [filename, content, title]
outputs: [status, file_path, bytes_written, filename]
side_effect: local_file_write
---
# export_md

Lưu câu trả lời, tóm tắt hoặc báo cáo nghiên cứu ra file Markdown (.md) cục bộ trên máy tính.

**Khi nào dùng:**
- Người dùng yêu cầu lưu, xuất hoặc ghi kết quả nghiên cứu/câu trả lời thành file Markdown (ví dụ: "xuất báo cáo này ra file md", "lưu tóm tắt vào file research.md", "export kết quả ra markdown").

**Khi nào KHÔNG dùng:**
- Định dạng dữ liệu thành digest để hiển thị ngay trong chat (dùng `format`).
- Gửi tin nhắn lên kênh Telegram (dùng `send`).
- Đọc nội dung từ file hoặc URL (dùng `fetch`).

