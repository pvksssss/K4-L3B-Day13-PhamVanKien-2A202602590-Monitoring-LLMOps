# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Tên file gợi ý:

```text
01-pytest.png
02-log-validator.png
03-dashboard-validator.png
04-structured-log.png
05-pii-redaction.png
06-trace-list.png
07-trace-waterfall.png
08-trace-metadata.png
09-prompt-versions.png
10-prompt-rollback.png
11-dashboard-overview.png
12-incident-metric.png
13-incident-log.png
14-incident-trace.png
```

Có thể dùng `.txt` cho output của tests/validators. Có thể tách dashboard thành nhiều ảnh nếu một ảnh không đọc rõ.

## Evidence hiện có và giới hạn

- `01-pytest.txt`, `02-log-validator.txt`, `03-dashboard-validator.txt`: output lần chạy trên commit source `564924d` bằng interpreter `.venv313`.
- `04-structured-log.txt`: hai event JSON thật cho `req-a11ce404`.
- `05-pii-redaction.txt`: input PII giả và hai event JSON đã scrub cho `req-a11ce405`.
- `06-trace-list.png`, `07-trace-waterfall.png`, `08b-generation.png`, `09-prompt-versions.png`: ảnh Langfuse đã được học viên cung cấp. Trace waterfall là trace CP2, không có correlation ID `req-a11ce404`.
- `08a-root-metadata.txt`, `10-prompt-promote-rollback.txt`, `11-dashboard-overview.txt`, `12-incident-metric.txt`, `13-incident-log.txt`, `14-incident-trace.txt`, `15-cp3-challenge-investigation.txt`: output/audit dạng text.
- Chưa có ảnh `08a`, `10a`, `10b`, `11`, `12` và `14` đúng như rubric yêu cầu. Dashboard hiện chưa có time-series latency panel; evidence metric hiện ghi rõ các số liệu và giới hạn, không giả làm ảnh chụp.

Ảnh `04`, `05`, `13` lấy từ terminal hoặc `data/logs.jsonl`. Ảnh `06`–`10`, `14` lấy từ project Langfuse cá nhân `day13-k4-l3b-<MSSV>` và nên nhìn thấy tên project. Không mở/chụp trang API Keys.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Trace waterfall](evidence/07-trace-waterfall.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
