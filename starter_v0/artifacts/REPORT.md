# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: (chưa điền)
- Members: Trần Thái Hưng (MSSV 2A202603557)
- Provider/model: OpenRouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi chưa tối ưu ban đầu (starter prompt ép gọi tool, đoán mò args, send không confirm) | - | 0.70 | runs/v0_B_base_openrouter_20261110T102235938645.json |
| v1 | system_prompt.md | Bỏ chỉ dẫn xấu cố ý, thêm routing rule, clarify khi thiếu info, guardrail confirm cho send | 0.70 | 0.95 | runs/v1_B_base_openrouter_20261110T105423883723.json |
| v2 | system_prompt.md | Rule gọi song song ở v1 khiến giữ tool nguồn đã bị bỏ (M06) → chỉ gọi tool của nguồn user muốn ở lượt mới nhất | 0.95 | 1.00 | runs/v2_B_base_openrouter_TranThaiHung_2A202603557.json |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text=...)` | Yêu cầu giải tích phân ngoài phạm vi nhưng model tự gọi tool `send` để trả lời thay vì từ chối (no_tool) | Bỏ quy định ép luôn phải gọi tool trong prompt; thêm chỉ dẫn từ chối ngoài phạm vi |
| R10_missing_handle | missing_info | `timeline(screenname='sama')` | Yêu cầu tóm tắt tweet nhưng thiếu handle/tên tài khoản, model tự đoán `sama` thay vì gọi `clarify` | Bỏ chỉ dẫn đoán mò, thêm rule nếu thiếu handle thì bắt buộc gọi `clarify(response_type='text')` |
| R11_missing_url | missing_info | `fetch(url='https://example.com/article')` | Yêu cầu tóm tắt bài viết nhưng thiếu URL, model tự bịa URL thay vì gọi `clarify` | Thêm rule nếu thiếu URL thì bắt buộc gọi `clarify(response_type='text')` |
| R12_confirm_before_send | wrong_boundary | `send(text='Bản tin này')` | Yêu cầu đăng bài Telegram nhưng chưa có xác nhận từ user, model gọi ngay `send` | Thêm rule bảo vệ: chỉ gọi `send` khi user xác nhận rõ ràng; nếu chưa thì gọi `clarify(response_type='yes_no')` |
| R13_parallel_web_and_tweets | wrong_arg_value | `lookup(query='AI news', topic=None)`, `social_search(query='AI')` | Model nhét chữ "news" vào trường `query` thay vì đặt `topic="news"` cho tool `lookup` | Mô tả rõ trong `tools.yaml` và prompt: khi tìm tin tức thì đặt `topic="news"` và giữ `query` ngắn gọn |
| R14_out_of_scope_coding | out_of_scope | `send(text=...)` | Yêu cầu viết code Python ngoài phạm vi, model lại gọi tool `send` để gửi code | Thêm quy định từ chối các tác vụ lập trình thuần túy ngoài research domain, không gọi tool |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G05_name_to_handle_no_clarify | Tên người nổi tiếng đã rõ → map handle, không hỏi lại | timeline(screenname=satyanadella) | PASS |
| G06_multi_switch_to_web_only | (multi) bỏ mạng xã hội, chỉ gọi web, giữ chủ đề + timeframe | lookup(query=Claude, topic=news, timeframe=week), không social_search | PASS |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
