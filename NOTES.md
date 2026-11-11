# Ghi chú phân tích · Day 04

Họ và tên: Lê Hoàng Sơn
MSSV: 2A202603662

## Cấu hình chạy và thay đổi hạ tầng

- Provider/model agent: `gemini` / `gemini-3.5-flash-lite` (Gemini API free tier, qua endpoint OpenAI compatibility).
- Judge: mặc định cùng provider/model với agent.
- Quota free tier: 500 requests/ngày, 15 requests/phút, 250.000 tokens/phút.
- **Thay đổi trong `providers.py` (chỉ `post_json`, không đổi agent loop, dataset hay grading):**
  - Giãn cách tối thiểu giữa các request bằng biến môi trường `PROVIDER_MIN_INTERVAL` (dùng `4.5` giây; mặc định `0` = không giãn cách). Có lock để an toàn khi chạy nhiều worker.
  - Retry tối đa 3 lần khi provider trả HTTP 429/500/503: ưu tiên header `Retry-After`, nếu không có thì chờ 15s, 30s, 45s (tối đa 60s/lần). Lỗi 4xx khác (key, model) vẫn báo lỗi ngay như cũ.
  - Lý do: giới hạn 15 requests/phút dễ bị vượt vì agent và judge gọi model liên tiếp; khi gặp 429, `run_agent` trả `error`, case thành `unscored` và điểm tổng thành `null`. Thay đổi này chỉ giảm lỗi hạ tầng, không ảnh hưởng nội dung câu trả lời hay cách chấm.
- Không sửa `fixtures/`, `evals/cases.json`, `evals/scenarios.py`, `evals/grading.py`. `eval_before.json` và `eval_after.json` dùng cùng cấu hình trên.

## 1. Case được chọn

- ID case:
- Câu trả lời của agent:
- Điểm ở lần chạy 1:

## 2. Bằng chứng trong trace

Dán đoạn trace chứng minh lỗi và nêu nguyên nhân có thể xảy ra.

```text

```

## 3. Thay đổi đã thực hiện

- Sửa gì, ở đâu:
- Vì sao chọn thay đổi này:

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng |  |  |
| Điểm case đã chọn |  |  |
| Số model calls |  |  |
| Token, chi phí nếu có |  |  |

- Lỗi đã giải quyết:
- Lỗi còn lại hoặc mới xuất hiện:

## 5. Giới hạn

Nêu giới hạn của điểm judge, của snapshot và của việc chỉ chạy một lần mỗi phiên bản.
