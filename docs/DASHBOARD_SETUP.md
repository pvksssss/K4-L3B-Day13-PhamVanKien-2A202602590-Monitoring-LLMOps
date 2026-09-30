# Dashboard local

[`../config/dashboard.yaml`](../config/dashboard.yaml) là contract của sáu panel: latency/TTFT, traffic, errors/retrieval, cost, tokens và quality. Dashboard trong `dashboard.py` đọc trực tiếp `data/logs.jsonl`, không gọi dịch vụ ngoài. Mỗi panel hiển thị đơn vị, threshold và cửa sổ 60 phút theo contract; dashboard tự làm mới mỗi 30 giây.

## Chạy

1. Cài dependencies trong `requirements.txt` và chạy API.
2. Tạo dữ liệu bằng `python scripts/load_test.py --concurrency 5`.
3. Mở dashboard:

```bash
streamlit run dashboard.py
```

4. Xác nhận đủ sáu panel và chạy validator:

```bash
python scripts/validate_dashboard.py
```

Dashboard xử lý file log chưa tồn tại như trạng thái rỗng, bỏ qua dòng JSONL malformed/ghi dở và hiển thị số dòng bị bỏ qua.

## Cách tính

| Panel | Cách tính |
|---|---|
| Latency | P50/P95/P99 và TTFT P95 trên `response_sent` |
| Traffic | Tổng `request_received` chia cho số phút cấu hình |
| Errors | `request_failed / request_received`; retrieval success trên event có `tool_success` boolean |
| Cost | Tổng cost và tổng theo phút trên `response_sent` |
| Tokens | Tổng input/output tokens trên `response_sent` |
| Quality | Mean `quality_score` trên `response_sent` |

Chỉ event có timestamp ISO-8601 hợp lệ bên trong time range mới được tổng hợp. Dùng `correlation_id` trong log để tìm trace liên quan trên Langfuse. Các practice scenario chỉ bật khi được phép trong bài lab; sau khi chạy, tắt scenario và đối chiếu panel với log cùng cửa sổ.
