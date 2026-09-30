# Alert runbooks

Các điều kiện máy đọc nằm trong [`../config/alert_rules.yaml`](../config/alert_rules.yaml). Cả ba alert gửi tới Slack `#k4-l3b-alerts`; owner ban đầu là vai trò `llmops-on-call`, cần ánh xạ sang người trực của môi trường triển khai.

## Alert 1 — HighLatencyP95

- **Severity / duration:** warning / 5 phút.
- **Điều kiện:** P95 `response_sent.latency_ms` > 3000 ms trong cửa sổ 5 phút. Đây là ngưỡng SLO latency.
- **Ảnh hưởng:** người dùng chờ phản hồi lâu; kéo dài làm request vượt SLO 3 giây.
- **Metrics:** xem dashboard latency, P95/P99, TTFT và tỷ lệ request trong cùng cửa sổ; kiểm tra có đủ traffic để percentile có ý nghĩa.
- **Logs:** lọc `response_sent` có latency cao, nhóm theo `correlation_id`, feature và model; so sánh TTFT để xác định chậm trước hay sau token đầu tiên.
- **Traces:** mở trace theo correlation ID; so thời lượng `retriever.search` và `llm.generate`, prompt label/version và model.
- **Mitigation:** nếu retrieval chiếm phần lớn, tắt practice incident đã được bật hoặc phục hồi cấu hình retrieval gần nhất. Nếu generation/prompt là nguyên nhân và trace xác nhận regression, chuyển production prompt về version ổn định trước đó; xác minh bằng trace mới.

## Alert 2 — RequestOrRetrievalFailures

- **Severity / duration:** critical / 5 phút.
- **Điều kiện:** error rate > 2% hoặc retrieval success < 90%, trên rolling 5 phút và ít nhất 20 request.
- **Ảnh hưởng:** request lỗi hoặc trả lời thiếu dữ liệu nguồn.
- **Metrics:** đối chiếu error rate, retrieval success và request volume; kiểm tra điều kiện tối thiểu 20 request.
- **Logs:** nhóm `request_failed` theo `error_type`, `tool_name`, `tool_success`; tìm correlation ID của lỗi đầu tiên và xác định lỗi có tập trung theo feature/model không.
- **Traces:** kiểm tra trace lỗi tương ứng, trạng thái và duration retriever, sau đó đối chiếu lỗi generation nếu retrieval thành công.
- **Mitigation:** khôi phục vector store/retrieval endpoint hoặc cấu hình hoạt động gần nhất; tắt practice failure nếu đang bật; nếu lỗi thuộc upstream model, áp dụng fallback đã được hỗ trợ và theo dõi error rate trước khi đóng alert.

## Alert 3 — QualityOrCostGuardrail

- **Severity / duration:** warning / 10 phút.
- **Điều kiện:** mean `quality_score` < 0.75 trong rolling 10 phút hoặc tổng `cost_usd` rolling 24 giờ > 2.50 USD. Nhánh chi phí phải duy trì quá ngưỡng 10 phút trước khi alert fire.
- **Ảnh hưởng:** chất lượng câu trả lời suy giảm hoặc ngân sách vận hành vượt guardrail.
- **Metrics:** xác định nhánh nào kích hoạt; xem mean quality, response count, token input/output và rolling daily cost.
- **Logs:** đối chiếu quality/cost theo correlation ID, model, feature, `tokens_in`, `tokens_out`; xác nhận không phải dữ liệu thiếu hoặc workload thử nghiệm.
- **Traces:** so prompt label/version, token usage và output preview đã scrub trên trace đại diện; kiểm tra khác biệt candidate so với baseline.
- **Mitigation:** nếu trace cho thấy prompt candidate làm quality giảm, rollback production về baseline đã xác minh. Nếu chi phí tăng do token output, phục hồi prompt/model config ổn định hoặc giảm tải thử nghiệm; xác minh quality/cost sau mitigation.

## SLO và error budget

SLO chính: 99.5% request đạt `response_sent` trong 3000 ms trên cửa sổ 28 ngày. Error budget là 0.5% số request; với 10,000 request, tối đa 50 request không đạt SLO. Alert latency là cảnh báo sớm theo cửa sổ ngắn, không thay thế phép tính SLI 28 ngày.
