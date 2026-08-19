# ArtTools — Vers For Vietnamese

Trợ lý lập trình desktop (PyQt6): hỏi-đáp AI để sinh code, chạy/test code
ngay trong app, rà lỗi bằng AI, chatbot, và theo dõi tài nguyên hệ thống —
tất cả trong một sidebar duy nhất.

Repo có **2 bản**:

| File | Trạng thái | Khác biệt |
|---|---|---|
| `ArtToolsv2.py` | ✅ Khuyến nghị dùng bản này | Trang Manager chỉ theo dõi CPU & RAM — ổn định |
| `ArtTools.py` | ⚠️ Bản có theo dõi GPU nhưng đang lỗi | Thêm theo dõi GPU rời (qua `nvidia-smi`) và GPU tích hợp (qua sysfs Linux), nhưng phần đọc tải GPU chưa hoạt động đúng |

Nếu không cần theo dõi GPU, luôn chạy `ArtToolsv2.py`.

## Tính năng

| Trang | Mô tả |
|---|---|
| 💬 Code AI | Sinh code theo yêu cầu, chọn ngôn ngữ (Python / C++ / Lua / Luau) và model (Free / Claude / DeepSeek / ChatGPT) |
| ▶ Run / Test | Chạy trực tiếp code vừa sinh — hỗ trợ Python (interpreter hệ thống), C++ (biên dịch bằng `g++`), Lua/Luau (`lua` hoặc `luau`); có ô nhập stdin khi chương trình đang chạy |
| 🔍 Error Check | Đưa code cho AI review: lỗi cú pháp, logic, edge case, hiệu năng — trả lời tiếng Việt kèm code sửa |
| 🗨 Chat Bot | Chat tự do với AI ngay trong app |
| 📊 Manager | Theo dõi CPU, RAM (và GPU ở bản `ArtTools.py`), pin, danh sách tiến trình |
| ❄ Effect | Hiệu ứng nền: Tuyết rơi / Mưa / Lá rơi |
| 🔑 Settings | Nhập API key, chọn model AI mặc định, xem thông tin cấu hình |

## Yêu cầu

- Python 3.9+
- Thư viện Python:

```bash
pip install PyQt6 requests psutil gputil
```

- Để dùng tính năng **Run / Test**:
  - C++ cần có `g++` trong PATH.
  - Lua/Luau cần có `lua` hoặc `luau` trong PATH.
  - Python dùng thẳng interpreter hệ thống, không cần cài thêm.
- Để theo dõi GPU rời NVIDIA (chỉ bản `ArtTools.py`): cần `nvidia-smi` có sẵn
  trong PATH (đi kèm driver NVIDIA).

## Chạy chương trình

```bash
python ArtToolsv2.py
```

## Model AI

- **Free**: dùng API miễn phí công khai, không cần key — chất lượng có thể
  thay đổi tùy nhà cung cấp.
- **Claude / DeepSeek / ChatGPT**: cần nhập API key riêng của bạn ở trang
  Settings.

## Cấu hình

Lưu tại:

- Windows: `%APPDATA%\ArtTools\config.json`
- Linux/macOS: `~/.config/ArtTools/config.json`

⚠️ File này chứa API key nếu bạn đã nhập — **không commit/chia sẻ file
config.json** này lên đâu công khai.

## Lưu ý

- README bản gốc của repo có ghi nhầm lệnh chạy là `ArtTools.py` cho cả 2
  bản — README này đã sửa đúng: chạy `ArtToolsv2.py` (bản ổn định) hoặc
  `ArtTools.py` (bản có GPU nhưng còn lỗi tải GPU), tùy nhu cầu.
- Tính năng "Free" (không cần API key) gọi một API bên thứ ba công khai
  (`chateverywhere.app`) — có thể ngừng hoạt động bất cứ lúc nào ngoài tầm
  kiểm soát của repo này; nếu gặp lỗi, chuyển sang model có API key riêng.
