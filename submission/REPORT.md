# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:**
- **MSSV:**
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-<MSSV>`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/09-pytest-cp2.txt` |
| Log validator | `evidence/07-log-validator-cp2.txt` |
| Dashboard validator | `evidence/08-dashboard-validator-cp2.txt` |
| Structured log | `evidence/04-structured-log-cp1.txt` |
| PII redaction | `evidence/05-pii-redaction-cp1.txt` |
| Trace list, hierarchy, prompt rollback IDs | `evidence/06-langfuse-trace-audit-cp2.txt` |
| Dashboard runtime | `evidence/10-dashboard-runtime-cp2.txt` |
| CP3 incident metric/log/trace | `evidence/15-cp3-challenge-investigation.txt` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | CP1: 20 records | **100/100** | 90 records, 42 correlation IDs, thiếu field/enrichment: 0, PII leak: 0 |
| `validate_dashboard.py` | Chưa dựng runtime | **6/6 panel** | Contract validator pass |
| `pytest` | CP1: 26 passed | **36 passed** | Python 3.13.15 |
| Số traces hợp lệ | Chưa có | **22 traces / 66 observations** | 22 AGENT, 22 RETRIEVER, 22 GENERATION |
| Số PII leak | CP1: 0 | **0** | Log validator và audit 66 Langfuse observations |
| Latency P95 / TTFT P95 | Chưa ghi nhận | **933.1 ms / 50 ms** | Từ 32 response logs trong cửa sổ 60 phút |
| Retrieval success rate | Chưa ghi nhận | **100%** | Event `tool_success` trong log |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware chấp nhận `x-request-id` đúng dạng `req-<8 ký tự hex>`, chuẩn hóa chữ thường; nếu thiếu hoặc sai định dạng thì sinh ID mới. ID được bind vào structlog contextvars, đưa vào response header `x-request-id`, `x-response-time-ms` và body `correlation_id`.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash` (SHA-256 rút gọn 12 ký tự), `session_id`, `feature`, `model`, `env`, event, timestamp và level.
- **Cách bảo đảm PII được scrub trước khi ghi:** Structlog chạy processor đệ quy trên mọi giá trị chuỗi trong dict/list trước JSONL writer; pattern che email, điện thoại Việt Nam, CCCD 12 số và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** `python -m pytest -q` — 26 passed; `python scripts/validate_logs.py` — 100/100, 10 correlation IDs, 0 field thiếu, 0 PII leak. Log mẫu đã scrub ở `evidence/04-structured-log-cp1.txt` và `evidence/05-pii-redaction-cp1.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project đã cấu hình ở `.env`:** Dùng Langfuse CLI/API để đọc 22 trace mới, mỗi trace có một agent root cùng retriever và generation child. Không đưa credential vào log/repository.
- **Cấu trúc root/retrieval/generation observations:** trace `day13-agent-request` có root observation `lab-agent-run` (AGENT), cùng hai child `retriever.search` (RETRIEVER) và `llm.generate` (GENERATION); sample trace đã kiểm tra có input/output preview scrub, model, prompt version, token usage, estimated cost và correlation ID.
- **Cách nối trace với log:** `correlationId` trong trace metadata trùng `correlation_id` trong JSONL.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, labels `baseline` và `production` sau rollback.
- **Version/label candidate:** version 2, label `candidate`; đã thử gán `production` rồi rollback.
- **Trace ID của baseline/candidate/promote/rollback:** `1cb81f87d5f8cdf8a72e94e17bcd0ef8` / `c3a4ebc7b14e2bc70f4d4de113a3f0ee` / `10f1e751653c9efad7fc86bfe7bcf3e3` / `e89c0c5a4bf91ee8b3c9e8dfd790bc5a`. Correlation IDs và version đối chiếu tại `evidence/06-langfuse-trace-audit-cp2.txt`.
- **Cách promote và rollback `production`:** gán label `production` cho version 2, tạo trace xác nhận promptVersion 2; chuyển label về version 1, khởi động client mới để tránh prompt cache cũ và xác nhận trace rollback promptVersion 1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `dashboard.py` dùng Streamlit và đọc `data/logs.jsonl`: latency/TTFT, traffic, errors/retrieval, cost, tokens và quality. AppTest xác nhận sáu panel render không lỗi; time range 60 phút có 32 request/response.
- **SLO và lý do chọn:** 99.5% request thành công trong ≤3000 ms trong 28 ngày, khớp ngưỡng P95 của dashboard và ưu tiên độ trễ người dùng.
- **Cách tính error budget:** 0.5%; với 10,000 request cho phép tối đa 50 request không đạt mục tiêu SLO.
- **Ba alert và runbook tương ứng:** `HighLatencyP95`, `RequestOrRetrievalFailures`, `QualityOrCostGuardrail`; ngưỡng/thời lượng ở `config/alert_rules.yaml`, cách điều tra Metrics → Logs → Traces tại `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

Challenge file chính thức được giữ local, không commit/push. Báo cáo và số liệu đầy đủ nằm trong [evidence/15-cp3-challenge-investigation.txt](evidence/15-cp3-challenge-investigation.txt).

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-30 05:18:13Z–05:18:28Z (12:18:13–12:18:28 Asia/Ho_Chi_Minh)
- **Triệu chứng từ metrics:** 5/5 request vượt 2000 ms; P50 2652 ms, P95 3451 ms.
- **Log line và correlation ID liên quan:** `response_sent`, `req-44cd714c`, 3451 ms; log và các ID khác trong evidence CP3.
- **Trace ID và span gây ảnh hưởng:** `2e9821ffc0b22941f04c53a1a9f5ac6d`, `retriever.search` span `aac647478c39fd4e`, 2501 ms.
- **Root cause:** Incident `rag_slow` chèn `time.sleep(2.5)` vào retrieval; generation khoảng 152 ms.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable`; request xác minh sau đó hoàn tất trong 152 ms.
- **Preventive measure:** Giữ HighLatencyP95 >3000 ms / 5 phút và runbook metrics → logs → traces; theo correlation ID để so thời lượng retrieval với generation.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Dashboard runtime và Langfuse trace/prompt audit có evidence dạng text; ảnh dashboard chưa có trong evidence.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
