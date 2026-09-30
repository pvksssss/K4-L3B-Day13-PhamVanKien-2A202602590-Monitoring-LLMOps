# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Phạm Văn Kiên
- **MSSV:** 2A202602590
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/pvksssss/K4-L3B-Day13-PhamVanKien-2A202602590-Monitoring-LLMOps
- **Commit SHA source đã kiểm thử:** `564924d` (commit follow-up chỉ thêm evidence và cập nhật report)
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602590`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log (`correlation_id=req-a11ce404`) | `evidence/04-structured-log.txt` |
| PII redaction (`correlation_id=req-a11ce405`) | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace tree for request 04 (`req-a11ce404`) | `evidence/07-trace-waterfall.jpg`, `evidence/07-trace-waterfall-audit.txt` |
| Root metadata for request 04 | `evidence/08a-root-metadata.jpg`, `evidence/08a-root-metadata.txt` |
| Generation for request 04 | `evidence/08b-generation.jpg`, `evidence/08b-generation-preview.jpg`, `evidence/08b-generation-audit.txt` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Promote v2 screenshot and earlier promote/rollback trace audit | `evidence/10a-prompt-promoted.jpg`, `evidence/10-prompt-promote-rollback.txt` |
| Dashboard overview (live UI text capture; PNG missing) | `evidence/11-dashboard-overview.txt` |
| Incident metric (text; dashboard time series screenshot missing) | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace (slow retrieval and matching `req-44cd714c`) | `evidence/14-incident-trace.jpg`, `evidence/14-incident-trace.txt` |
| Full CP3 investigation | `evidence/15-cp3-challenge-investigation.txt` |
| Langfuse Home bổ sung: tổng quan, usage/cost, latency percentiles | `evidence/16a-langfuse-home-overview.png`, `evidence/16b-langfuse-home-usage.png`, `evidence/16c-langfuse-home-latency.png` |

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
- **Version/label baseline:** version 1, label `baseline`. Audit CP2 ghi nhận một lần rollback đã đưa `production` về v1.
- **Version/label candidate:** version 2, label `candidate`. Ảnh mới `10a-prompt-promoted.jpg` ghi nhận lần promote tiếp theo đưa `production` sang v2; phiên Computer Use bị dừng trước khi rollback lần này, nên trạng thái Langfuse cuối cùng đã quan sát là v2 `production`.
- **Trace ID của baseline/candidate/promote/rollback:** `1cb81f87d5f8cdf8a72e94e17bcd0ef8` / `c3a4ebc7b14e2bc70f4d4de113a3f0ee` / `10f1e751653c9efad7fc86bfe7bcf3e3` / `e89c0c5a4bf91ee8b3c9e8dfd790bc5a`. Correlation IDs và version đối chiếu tại `evidence/06-langfuse-trace-audit-cp2.txt`.
- **Cách promote và rollback `production` trong lần CP2 trước:** gán label `production` cho version 2, tạo trace xác nhận promptVersion 2; chuyển label về version 1, khởi động client mới để tránh prompt cache cũ và xác nhận trace rollback promptVersion 1. Lần promote để chụp ảnh 10a sau đó chưa được rollback.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `dashboard.py` dùng Streamlit và đọc `data/logs.jsonl`: latency/TTFT, traffic, errors/retrieval, cost, tokens và quality. AppTest xác nhận sáu panel render không lỗi; time range 60 phút có 32 request/response. Ba ảnh Langfuse Home 16a–16c bổ sung thống kê trace, usage/cost và latency percentiles, không phải ảnh dashboard Streamlit sáu panel.
- **SLO và lý do chọn:** 99.5% request thành công trong ≤3000 ms trong 28 ngày, khớp ngưỡng P95 của dashboard và ưu tiên độ trễ người dùng.
- **Cách tính error budget:** 0.5%; với 10,000 request cho phép tối đa 50 request không đạt mục tiêu SLO.
- **Ba alert và runbook tương ứng:** `HighLatencyP95`, `RequestOrRetrievalFailures`, `QualityOrCostGuardrail`; ngưỡng/thời lượng ở `config/alert_rules.yaml`, cách điều tra Metrics → Logs → Traces tại `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

Challenge file chính thức được giữ local, không commit/push. Báo cáo và số liệu đầy đủ nằm trong [evidence/15-cp3-challenge-investigation.txt](evidence/15-cp3-challenge-investigation.txt).

- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Khoảng thời gian điều tra:** 2026-09-30 05:18:13Z–05:18:28Z (12:18:13–12:18:28 Asia/Ho_Chi_Minh)
- **Triệu chứng từ metrics:** 5/5 request vượt 2000 ms; P50 2652 ms, P95 3451 ms.
- **Log line và correlation ID liên quan:** `response_sent`, `req-44cd714c`, 3451 ms; log và các ID khác trong evidence CP3.
- **Trace ID và span gây ảnh hưởng:** `2e9821ffc0b22941f04c53a1a9f5ac6d`, `retriever.search` span `aac647478c39fd4e`, 2501 ms.
- **Đối chiếu Langfuse Home:** ảnh 16c hiển thị P95 retrieval 2,50 s, generation 0,15 s và trace 2,65 s trong khoảng 1 ngày; đây là số tổng hợp hỗ trợ kết luận, không thể hiện baseline và incident trên cùng biểu đồ latency theo thời gian.
- **Root cause:** Incident `rag_slow` chèn `time.sleep(2.5)` vào retrieval; generation khoảng 152 ms.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable`; request xác minh sau đó hoàn tất trong 152 ms.
- **Preventive measure:** Giữ HighLatencyP95 >3000 ms / 5 phút và runbook metrics → logs → traces; theo correlation ID để so thời lượng retrieval với generation.

- **Evidence correlation ID tự đặt cho structured-log:** `req-a11ce404`; PII test: `req-a11ce405`. Request `req-a11ce404` đã chạy qua API có `.env` và được xác nhận trên Langfuse: trace `6d434500bee8ad07aa474e87b37043ba`; metadata gốc và generation audit nằm trong evidence 07/08. Request PII `req-a11ce405` chỉ chạy cục bộ để kiểm tra scrub, không gửi sang Langfuse. CP3 trace/log correlation riêng là `req-44cd714c`.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Thiết kế và triển khai cơ chế PII scrubbing đệ quy (`scrub_pii_processor` trong `app/logging_config.py` và `app/pii.py`) ngay tại tầng structlog processor trước khi serialize JSON hoặc ghi file/console. Quyết định này bảo đảm nguyên tắc "privacy by design": mọi dữ liệu nhạy cảm của người dùng (email, số điện thoại Việt Nam, CCCD 12 số, thẻ thanh toán) đều được nhận diện bằng regex và thay thế bằng các token `[REDACTED_*]` trên toàn bộ các cấu trúc dữ liệu lồng nhau (dict, list, string) trước khi log ghi xuống đĩa hoặc chuyển tới bất kỳ hệ thống phân tích/giám sát bên ngoài nào, ngăn chặn triệt để nguy cơ rò rỉ PII.
- **Một lỗi/blocker đã gặp:** Trong quá trình triển khai CP2 và chạy workload, gặp lỗi rớt kết nối mạng hoặc môi trường local chặn HTTPS tới Langfuse Cloud OTel endpoint (`[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions` / connection pool retry error). Ngoài ra, trace ban đầu chỉ ghi nhận root observation mà chưa phân tách cây quan hệ cha - con cho retrieval và generation.
- **Cách tìm nguyên nhân và xử lý:** Đọc kỹ traceback và tài liệu Langfuse SDK v4; cô lập cấu hình OTel batch exporter để không làm sập tiến trình chính của ứng dụng khi mạng chập chờn; dùng structlog contextvars để lưu giữ `correlation_id` xuyên suốt vòng đời request. Đồng thời, tái cấu trúc hàm `LabAgent.run` sử dụng observation API của Langfuse v4 để tạo rõ ràng root observation kiểu `AGENT` (`lab-agent-run`) và 2 child observation: `retriever.search` (`RETRIEVER`) và `llm.generate` (`GENERATION`). Khi thực hiện kiểm thử promote/rollback prompt, sử dụng client phiên bản mới để tránh dính cache prompt cục bộ.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics (What is broken?):** Đóng vai trò lớp cảnh báo đầu tiên (Detection). Giúp quan sát xu hướng cấp độ vĩ mô của toàn hệ thống (ví dụ: P95 latency vọt từ ~933ms lên 3451ms, vi phạm ngưỡng SLO 3000ms, tỷ lệ lỗi...).
  - **Logs (When & Which request?):** Đóng vai trò thu hẹp phạm vi điều tra (Correlation & Context). Dựa vào khoảng thời gian xảy ra đột biến trên Metrics, lọc file `data/logs.jsonl` để định vị chính xác request bị ảnh hưởng thông qua `correlation_id` (ví dụ `req-44cd714c`), qua đó biết được context cụ thể (thời điểm, user_id_hash, event `response_sent`, latency thực tế).
  - **Traces (Where & Why?):** Đóng vai trò chẩn đoán nguyên nhân gốc rễ (Deep dive & Root cause). Sử dụng `correlation_id` tra cứu sang hệ thống tracing phân tán (Langfuse trace `2e9821ffc0b22941f04c53a1a9f5ac6d`), mở cây waterfall để xem từng span thành phần. Nhờ đó phát hiện ngay span `retriever.search` chiếm tới 2501 ms trong khi span `llm.generate` chỉ mất 152 ms, xác định chính xác sự cố nằm ở tầng retrieval của RAG chứ không phải do mô hình LLM sinh text chậm.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt Versioning & Rollback:* Quản lý prompt như mã nguồn (v1, v2) với các nhãn `baseline`, `candidate`, `production`. Cho phép kiểm thử prompt mới (v2) và nếu phát hiện chất lượng câu trả lời giảm sút hoặc latency tăng cao, có thể lập tức rollback nhãn `production` về v1 mà không cần sửa code hay deploy lại ứng dụng backend.
  - *Token & Cost Monitoring:* LLM tính phí theo lượng token input và output. Việc giám sát liên tục token/cost giúp phát hiện sớm các hiện tượng prompt injection, context bloat (nhồi context quá lớn) hoặc vòng lặp vô tận, giúp kiểm soát ngân sách vận hành và phát hiện các truy vấn bất thường.
  - *SLO & Error Budget:* Định lượng cam kết chất lượng dịch vụ (ví dụ: 99.5% request đạt latency <= 3000ms trong 28 ngày, error budget 0.5%). Error budget là "ngân sách rủi ro" giúp đội ngũ phát triển quyết định khi nào được phép thử nghiệm tính năng/prompt mới và khi nào phải tạm dừng release để tập trung tối ưu độ ổn định.
- **Điều quan trọng nhất đã học:** Hiểu sâu sắc và thực hành trọn vẹn kiến trúc Observability trong hệ thống LLMOps/GenAI: sự kết hợp nhịp nhàng giữa Structured Logging (với Correlation ID xuyên suốt), PII Redaction tự động, Tracing phân tán (cây quan hệ Agent - Retriever - Generation trên Langfuse) và Dashboard giám sát theo SLO. Chuỗi điều tra chuẩn Metrics -> Logs -> Traces giúp khoanh vùng và giải quyết sự cố kỹ thuật một cách khoa học, chính xác thay vì phỏng đoán.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Ảnh `06-trace-list.png`, `07-trace-waterfall.png`, `08b-generation.png` và `09-prompt-versions.png` do học viên cung cấp trước đó; ảnh 07/08b PNG là CP2 sample. Ảnh JPG mới 07/08a/08b khớp request `req-a11ce404`; ảnh 14 khớp log CP3 `req-44cd714c` và cho thấy retrieval 2,50 giây. Ảnh 10a ghi nhận v2 `production`, nhưng chưa có ảnh 10b sau rollback lần promote này; trạng thái cuối quan sát được vẫn là v2 `production`. Ba ảnh Langfuse Home 16a–16c là evidence bổ sung, không thay thế ảnh dashboard Streamlit sáu panel 11 hoặc biểu đồ latency incident 12. Hai mục 11/12 vẫn thiếu PNG đúng rubric. Theo lựa chọn của học viên, không thay đổi dashboard; latency vẫn là số tổng hợp và chưa có biểu đồ theo thời gian thể hiện baseline và incident cùng trục. Generation trong Langfuse hiển thị `prompt_preview`/`answer_preview`, nên ảnh 08b không đáp ứng tiêu chí Input/Output trống.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
