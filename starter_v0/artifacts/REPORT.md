# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

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
| `clarify` | hỏi lại người dùng khi thiếu thông tin | không |
| `timeline` | lấy các tweet gần đây của một tài khoản Twitter | không |
| `social_search` | tìm kiếm tweet thảo luận theo từ khóa | không |
| `lookup` | tra cứu thông tin và tin tức trên web | không |
| `fetch` | đọc toàn bộ nội dung một URL bài viết | không |
| `format` | trình bày dữ liệu thành văn bản digest | không |
| `send` | đăng bản tin lên Telegram channel (khi có xác nhận) | không |
| `policy` | tra cứu chính sách công ty nội bộ | không |
| `papers` | tìm kiếm bài báo khoa học trên arXiv | không |
| `paper_text` | tải và trích xuất text từ PDF arXiv | không |
| `export_md` | xuất câu trả lời, báo cáo nghiên cứu ra file Markdown (.md) cục bộ | **có (mới)** |

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
| v2 | system_prompt.md + tools.yaml | Tối ưu routing tool và xử lý out-of-scope | 0.95 | 0.70 | runs/v2_B_base_openrouter_20261110T172431333437.json |
| v3 | system_prompt.md + tools.yaml | Đánh giá v3 trên cùng artifact (xác nhận độ ổn định) | 0.70 | 0.75 | runs/v3_B_base_openrouter_20261110T172621085552.json |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

Nguồn: `runs/v0_B_base_openrouter_20261110T102235938645.json` (`v0+peb1c8179815b+t5b22a2476d41`, `openai/gpt-4o-mini`): 14/20 PASS, `case_accuracy=0.70`, `tool_routing=0.75`, `argument=0.70`. Cột *Actual Tool Calls* và *failures* chép từ `results[*].result`; câu trích trong *What Failed* là nguyên văn starter prompt (`ff7427d:starter_v0/artifacts/system_prompt.md`).

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="Nguyên hàm của x^2 là \frac{x^3}{3} + C ...")` | `unexpected_tool_call` — "expected no tool call". Case `no_tool` nên eval **không** ép `tool_choice`, nhưng model vẫn gọi `send` để "giao" lời giải toán. Gốc: starter prompt ép *"Always finish the request in a single step. Pick one tool"* → model coi việc gọi tool là bắt buộc, và `send` là tool duy nhất "trả kết quả ra ngoài". | v1 prompt **§1 Scope & Meta Inquiries**: định nghĩa rõ toán/code là out-of-scope → từ chối bằng text, **DO NOT CALL ANY TOOLS**, *"NEVER call `send` … to deliver math or code"*; xoá câu *"Pick one tool"*. |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | `missing_tool_call` — "missing tool call clarify", "extra tool call timeline". Model đoán đúng tài khoản mà starter prompt **gợi ý sẵn**: *"pick a well-known account like Sam Altman"* + *"do not ask them back — just make a sensible guess"*. Lời gọi đoán còn trả `HTTPError` → user nhận lỗi thay vì câu hỏi. | v1 prompt **§2 Clarification**: *"NEVER guess or invent missing essential information"*; thiếu account → `clarify(response_type="text")`, cấm chọn account mặc định (nêu đích danh Sam Altman). |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | `missing_tool_call` — "missing tool call clarify", "extra tool call fetch". Starter prompt dặn *"If you only have a vague reference like 'this article', assume a likely URL and read it"* → model bịa URL. Nguy hiểm hơn R10: `fetch` **chạy thành công** trên trang bịa nên agent sẽ tóm tắt sai nội dung mà không có lỗi nào báo hiệu. | v1 prompt **§2**: thiếu URL → `clarify(response_type="text")` xin link, cấm bịa URL (nêu đích danh `example.com`). |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này")` | `missing_tool_call` — "missing tool call clarify", "extra tool call send". Starter prompt: *"When the user wants to send, post, or publish something, just go ahead and do it"* → bỏ qua bước xác nhận của hành động ghi ra ngoài; nội dung gửi đi chỉ là chuỗi vô nghĩa `"Bản tin này"` (model không có bản tin nào để đăng). Chỉ nhờ guardrail **trong code** (`send` trả `needs_confirmation` khi `confirmed=false`) nên không có tin nào bị đăng thật. | v1 prompt **§3 Safety Guardrail & Actions**: chưa có xác nhận → `clarify(response_type="yes_no")`; chỉ gọi `send(confirmed=true)` sau khi user đồng ý rõ ràng. Guardrail code giữ nguyên làm lớp bảo vệ thứ hai. |
| R13_parallel_web_and_tweets | wrong_arg_value | `lookup(query="AI news", timeframe="day", max_results=5)`, `social_search(query="AI", search_type="Latest", limit=5)` | Routing **đúng** (đủ 2 tool) nhưng sai arg: "query: expected 'AI', got 'AI news'", "topic: expected 'news', got None". `tools.yaml` v0 chỉ mô tả `topic` là *"Phân loại"* (default `general`) → model không biết `topic=news` dùng cho tin tức, nên nhét "news" vào `query`. | v1 prompt **§4 Tool Routing & Parameter Conventions** (`lookup`): tin tức → `topic="news"`, giữ `query` là chủ đề lõi, *"do not repeat 'news' inside query"*; map "hôm nay" → `timeframe="day"`. Sửa bằng **prompt**, `tools.yaml` chưa đổi ở v1 (cùng `tools_hash=5b22a2476d41`). |
| R14_out_of_scope_coding | out_of_scope | `send(text="def fibonacci(n): ...")` | `unexpected_tool_call` — "expected no tool call". Cùng gốc với R08: model viết code rồi đẩy qua `send` thay vì từ chối. 2 case out-of-scope đều kết thúc ở `send` cho thấy đây là lỗi hệ thống của prompt, không phải ngẫu nhiên. | v1 prompt **§1**: coding implementation (ví dụ Fibonacci) là out-of-scope → từ chối, không gọi tool. |

**Từ log đến giả thuyết (evidence-driven):**

1. Gom 6 case FAIL theo `observed_mismatch`: 2 `unexpected_tool_call` (R08, R14), 3 `missing_tool_call` (R10, R11, R12), 1 `wrong_arg_value` (R13).
2. Đặt `actual_tool_calls` cạnh starter prompt: 5/6 lỗi khớp **từng câu** chỉ dẫn xấu — *"just make a sensible guess"* + *"like Sam Altman"* → R10 (`sama`); *"assume a likely URL"* → R11 (`example.com`); *"just go ahead and do it"* → R12; *"Pick one tool"* → R08/R14 (`send`). Lỗi thứ 6 (R13) không đến từ câu nào trong prompt mà từ việc **thiếu** quy ước arg `topic`.
3. Giả thuyết v1: *prompt starter chủ động xúi model đoán / tự gửi / luôn gọi tool, và thiếu quy ước arg cho `lookup`*. Kiểm chứng bằng cách **chỉ sửa `system_prompt.md`**, giữ nguyên `tools.yaml` để biết chắc mọi thay đổi metric là do prompt.

**Kết quả sau fix** — `runs/v1_B_base_openrouter_20261110T105423883723.json` (`v1+p021dbcd166f1+t5b22a2476d41`):

| Case | v0 | v1 | Hành vi v1 thực tế |
|---|---|---|---|
| R08 | FAIL | PASS | Không gọi tool, từ chối giải toán bằng text |
| R10 | FAIL | PASS | `clarify(response_type="text")` — "Bạn muốn tóm tắt tweet của tài khoản nào?" |
| R11 | FAIL | PASS | `clarify(response_type="text")` xin link bài viết |
| R12 | FAIL | PASS | `clarify(response_type="yes_no")` — "Bạn có xác nhận muốn đăng bản tin này lên Telegram không?" |
| R13 | FAIL | PASS | `lookup(query="AI", topic="news", timeframe="day")` + `social_search(query="AI")` |
| R14 | FAIL | PASS | Không gọi tool, từ chối viết code bằng text |

Metric: `case_accuracy` 0.70 → **0.95** (19/20), `tool_routing` 0.75 → 0.95, `argument` 0.70 → 0.95. Cả 6/6 case FAIL của v0 đều PASS, tức giả thuyết được xác nhận.

Đổi lại, `multiturn_accuracy` giảm 1.00 → 0.83: **M06_switch_tool** mới FAIL (`extra_tool_call` — user đã nói *"Bỏ Twitter"* nhưng model vẫn gọi thêm `social_search(query="OpenAI")`). Nguyên nhân khả dĩ là rule *Parallel Tool Calls* mới ở §4 khiến model gọi thêm nguồn. Đây là bằng chứng cho giả thuyết tiếp theo: v2 thêm rule *Multi-turn Priority & Tool Switching* (ưu tiên lượt mới nhất, bỏ tool cũ khi user đổi hướng). Kết quả v2 trên bộ base sẽ ghi ở B1.

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single-turn + 5 multi-turn), chạy bằng prompt v2 + `openai/gpt-4o-mini` (`runs/v2_B_group_openrouter_TranThaiHung_2A202603557_10cases.json`): **8/10 PASS (case_accuracy 0.80, tool_routing 1.00, argument 0.80, multiturn 1.00)**.

**Single-turn (5)**

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_dat_format_thread | Dữ liệu đã có sẵn + yêu cầu trình bày dạng thread → không gọi tool tìm kiếm | `format(template=thread)` | PASS |
| G03_newest_papers_sort | "mới được đăng gần đây nhất" → sắp xếp theo ngày nộp | `papers(sort_by=submittedDate, max_results=3)` | **FAIL** (`wrong_arg_value`: model dùng `lastUpdatedDate`) |
| G05_web_search_month_timeframe | "tin tức" → `topic=news`, "trong tháng này" → `timeframe=month`, query ngắn | `lookup(query=DeepSeek, topic=news, timeframe=month)` | PASS |
| G07_name_to_handle_no_clarify | Người dùng đã nêu tên người nổi tiếng → map handle, không hỏi lại (chống over-clarify) | `timeline(screenname=satyanadella)` | PASS |
| G09_policy_source_citation | Hỏi quy định NỘI BỘ → dùng `policy`, không dùng `lookup` | `policy(policy_area=source_citation)` | **FAIL** (`wrong_arg_value`: đúng tool `policy` nhưng bỏ `policy_area`) |

**Multi-turn (5)**

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G02_dat_format_template_correction | Lượt 3 đổi template sections → bullets; chỉ chấm lượt cuối | `format(template=bullets)` | PASS |
| G04_papers_then_read_text | Lượt cuối muốn đọc paper đã tìm → `paper_text`, không gọi lại `papers`/`fetch` | `paper_text(max_pages=3)` | PASS |
| G06_multiturn_research_then_export | Sau nghiên cứu, yêu cầu lưu file md → route tới tool mới **`export_md`** | `export_md(filename=openai_report.md)` | PASS |
| G08_multi_switch_to_web_only | Người dùng bỏ mạng xã hội → chỉ gọi `lookup`, không gọi thừa `social_search`; carry chủ đề + timeframe | `lookup(query=Claude, topic=news, timeframe=week)` | PASS |
| G10_multi_social_top_carryover | Carry 3 tham số qua 3 lượt: query (lượt 1), `search_type=Top` (lượt 2), `limit=3` (lượt 3) | `social_search(query=OpenAI, search_type=Top, limit=3)` | PASS |

**Nhận xét độ bao phủ**

- **Cân bằng:** 5 single (định tuyến + trích xuất tham số) / 5 multi (kế thừa ngữ cảnh, đổi ý định, sửa yêu cầu, bổ sung tham số).
- **Phủ 8/11 tool trong `tools.yaml`:** `format`, `papers`, `paper_text`, `lookup`, `timeline`, `social_search`, `policy`, `export_md`. Chưa có case riêng cho `fetch`, `send` (đã có R12/M04 ở bộ base), `clarify` (R10/R11 ở bộ base).
- **Tool mới `export_md`** được kiểm thử bởi G06 (PASS).
- **Loại lỗi:** `wrong_tool`, `wrong_arg_value`, `missing_info`, `unnecessary_tool` (chưa có `out_of_scope`/`wrong_boundary` ở bộ group, nhưng bộ base đã phủ).
- **Hai case FAIL là tín hiệu cần sửa, không phải case sai:** G03 và G13 cùng nguyên nhân gốc — `tools.yaml` chưa mô tả quy ước tham số (`sort_by` của `papers`, `policy_area` của `policy`); prompt v2 cũng chưa có rule routing cho hai tool này. Hướng sửa cho v3: bổ sung mô tả tham số/rule routing cho `papers` và `policy`.

## B4. Live Chat Evidence

Dẫn chứng từ các phiên tương tác trực tiếp thực tế qua giao diện chat / Streamlit UI:
- **File transcript chính**: `starter_v0/transcripts/v0_openrouter_20261110T111753577673.transcript.json`
- **File kết quả xuất bản**: `starter_v0/reports/openai_tweets_summary.md` (1,940 bytes)
- **Model**: `openai/gpt-4o-mini` qua OpenRouter

### Bảng minh chứng phiên tương tác Multi-turn (Session Evidence)

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tóm tắt 5 tweet mới nhất giúp mình" | *Không gọi tool bừa bãi* (Agent chủ động clarify) | Khắc phục lỗi đoán mò ở v0 (`sama`). Agent nhận diện thiếu username nên không đoán mò hay bịa account, dừng lại hỏi user. | Phản hồi: *"Bạn có thể cho mình biết tài khoản Twitter nào mà bạn muốn tóm tắt 5 tweet mới nhất không?"* |
| 2 | "của open ai" | `timeline(screenname="OpenAI", limit=5)` | Kế thừa ngữ cảnh multi-turn: trích xuất đúng account handle `OpenAI` từ "open ai", giữ nguyên số lượng `limit=5` từ lượt 1. | Lấy thành công 5 tweet thật từ API (Control Room, BioBasicsBench, GPT-6 Cyber...) và tóm tắt kèm link bài đăng. |
| 3 | "tôi muốn xuất câu trả lời sang md" | `export_md(filename="openai_tweets_summary.md", content=..., title="Tóm tắt tweet OpenAI")` | Kích hoạt đúng tool mới `export_md` được thêm ở v2. Không gọi nhầm sang `lookup`/`timeline`. Tự sinh tên file `.md` chuẩn. | Xuất file báo cáo thành công ra `starter_v0/reports/openai_tweets_summary.md`, giao diện Streamlit hiển thị nút tải file markdown ngay lập tức. |

### Phiên đối chứng bổ sung (Clarify Tool & Tin tức Web)
- **File transcript**: `starter_v0/transcripts/v1_openrouter_20261110T123830856900.transcript.json`
- **Lượt 1**: User hỏi *"tin tức hôm nay"* $\rightarrow$ Agent gọi tool `clarify(question="Bạn muốn tìm tin tức về chủ đề cụ thể nào như công nghệ, AI, kinh tế hay đời sống?", response_type="text")`.
- **Lượt 2**: User chọn *"công nghệ"* $\rightarrow$ Agent gọi `lookup(query="công nghệ", topic="news", timeframe="day", max_results=5)`, trả về 5 bài báo thời sự công nghệ mới nhất hôm nay từ `daidoanket.vn`, `baovinhlong.com.vn`,...

### Nhận xét trải nghiệm thực tế (User Experience Evaluation)
1. **Khả năng làm rõ thông tin thiếu (Clarification)**: Agent không còn tình trạng "tự đoán mù quáng" hay gọi tool vô tội vạ khi người dùng cung cấp thiếu thông tin (như thiếu tên tài khoản Twitter hoặc chủ đề tìm kiếm). Việc chủ động hỏi lại giúp người dùng định hướng câu hỏi chính xác mà không gặp lỗi API 400/404.
2. **Kế thừa ngữ cảnh hội thoại (Context Retention)**: Ở Turn 2, người dùng chỉ nhập vỏn vẹn "của open ai" nhưng Agent vẫn hiểu đầy đủ ý định "lấy 5 tweet mới nhất của tài khoản OpenAI" nhờ quản lý lịch sử hội thoại tốt.
3. **Kích hoạt tool mới mượt mà**: Ở Turn 3, Agent nhận diện chính xác yêu cầu xuất file báo cáo để gọi tool `export_md`, tự động định dạng Markdown có tiêu đề và danh sách liên kết, đáp ứng trải nghiệm trọn vẹn từ tìm kiếm $\rightarrow$ tổng hợp $\rightarrow$ xuất bản tài liệu.

## B5. Bonus Evidence

QA ngày **10/11/2026**. Các liên kết tính từ file báo cáo này; chỉ nhận kết quả có bằng chứng trong mã nguồn, run JSON hoặc transcript.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| UI Streamlit | [app.py](../app.py), [transcript](../transcripts/v0_openrouter_20261110T111753577673.transcript.json), [file xuất](../reports/openai_tweets_summary.md) | Chat nhiều lượt; chọn provider/model và version v0–v3; xem arguments/results trong execution log; nút download xuất hiện khi export thành công và file tồn tại. | v0/v1 dùng snapshot riêng; v2/v3 hiện dùng chung artifact, nên nhãn v3 chưa chứng minh bản tối ưu độc lập. Transcript chứng minh tool chạy; nút tải được đối chiếu qua code, chưa kiểm thử trình duyệt trong lần QA này. |
| Tool mới `export_md` | [TOOL.md](../tools/export_md/TOOL.md), [code](../tools/export_md/tool.py), [registry](../tools/__init__.py), [schema](tools.yaml), [tests](../tests/test_tools_todo.py), [eval G06](../data/eval_group.json), [run](../runs/v2_B_group_openrouter_TranThaiHung_2A202603557_10cases.json) | Frontmatter hợp lệ; đăng ký đầy đủ. Xuất UTF-8 có tiêu đề, tự thêm `.md`/sinh tên mặc định. G06 PASS với `export_md(filename="openai_report.md")`. | Thay ký tự phân cách đường dẫn, ghi dưới `reports/`; 5 input traversal kiểu Windows/Unix được kiểm tra không thoát thư mục đích. Nội dung rỗng bị từ chối; lỗi ghi trả error dict. Chưa chứng minh chống mọi tấn công filesystem như symlink. |
| Guardrail `send` | [code](../tools/send/tool.py), [prompt §3](system_prompt.md), [example test](../tests/test_tools_examples.py), [tests](../tests/test_tools_todo.py), [transcript chặn gửi](../transcripts/v0_openrouter_20261110T123023201746.transcript.json) | Prompt yêu cầu hỏi xác nhận. Code trả `needs_confirmation` khi chưa xác nhận; transcript lượt 2 có 2 lời gọi bị chặn. Test `confirmed=False` không phát HTTP; `confirmed=True` gửi đúng payload giả lập. | Chưa có bằng chứng gửi Telegram thật thành công sau xác nhận; nhánh thành công được mock. Code dựa vào cờ do caller truyền, chưa tự xác minh xác nhận gắn với nội dung/người dùng. |
| Company policy | [tool](../tools/policy/tool.py), [policy](../company_policy/source-citation-policy.md), [tests](../tests/test_tools_todo.py) | Query rỗng, lọc `policy_area` và tách câu injection khỏi `facts` sang `untrusted_text` đều PASS. | Test bộ lọc không chứng minh model luôn bỏ qua injection. arXiv/policy là tool có sẵn; lần QA này không chạy lại API arXiv/PDF. |

### Unit test và lỗi phát hiện

Chạy từ `starter_v0/`, offline; fixture chặn HTTP thật và test dùng mock:

```text
python -m pytest -q tests/test_tool_contract.py
60 passed

python -m pytest -q tests/test_tools_todo.py -k export_md
9 passed, 16 deselected

python -m pytest -q
92 passed
```

- Tổng **92 PASS, 0 FAIL, 0 SKIP**: 60 contract, 7 example và 25 test instance trong `test_tools_todo.py`.
- Hoàn thiện **14 hàm TODO**, thành 16 test instance nhờ parametrization input rỗng và `Top`/`Latest`. Giữ 3 test nền `export_md`, thêm 5 input đường dẫn và 1 lỗi ghi file: **9 test instance cho tool mới**.
- Cô lập toàn bộ test export bằng `tmp_path`, patch `ROOT` tại module sử dụng: không ghi đè báo cáo thật hoặc sinh bằng chứng giả.
- Phát hiện và sửa **1 bug trong tool mới**, **0 bug trong tool có sẵn được xác nhận**: Windows đổi LF thành CRLF khi `write_text`, nhưng `bytes_written` tính trước chuyển đổi. Regression test từng FAIL: **41 byte báo về / 44 byte trên đĩa**. Sửa bằng ghi buffer UTF-8 với `write_bytes`; assert `bytes_written == len(saved_path.read_bytes())` đã PASS.
- G06 chỉ chấm tool/filename nên có thể PASS dù số byte sai hoặc ghi file lỗi. Unit test kiểm tra nội dung file, vị trí lưu, số byte và nhánh `PermissionError`, bổ sung phần eval không chấm.

### Rà soát trước khi nộp

- [x] 60/60 contract test; toàn bộ suite 92/92, không còn skip.
- [x] `.env`, `.env.local`, `.env.production` bị ignore; `.env.example` vẫn được track. `git ls-files` không có `.env` thật hoặc biến thể `.env.*` ngoài `.env.example`.
- [x] Bổ sung ignore `*.pem`, `*.key`, `credentials.json`, `service-account*.json`, cache pytest trong `starter_v0/.gitignore`.
- [x] Quét nội dung file được Git theo dõi theo mẫu key OpenAI/OpenRouter, Google, GitHub, Telegram và private key: **0 kết quả**. Phạm vi là working tree được track theo mẫu, chưa kiểm toán lịch sử Git hay mọi loại secret.
- [x] Rà soát `git status` và `git diff --check`; giữ run/transcript làm bằng chứng, loại file ngoài phạm vi khỏi danh sách commit.
- [ ] Ngoài issue #13, nhóm còn cần hoàn thiện Team/A1/A3/link demo, B1 và version log v2/v3. Chưa có run base v2/v3 trong `runs/`; không điền metric thiếu log. B7 chỉ điền nếu thực sự làm local-model challenge.

README yêu cầu UI và **hơn 3 tool mới** cho bonus kết hợp: hiện mới có bằng chứng UI + một tool mới `export_md`, chưa đủ căn cứ nhận bonus đó. Không tính arXiv/policy có sẵn thành tool mới của nhóm.

## B6. Reflection

1. **Sửa hành vi hội thoại trong prompt và kiểm tra hồi quy.** Baseline 14/20 lên 19/20 sau khi sửa `system_prompt.md`: bỏ đoán account/URL, clarify và xác nhận trước gửi. Nhưng M06 gọi thừa `social_search` khi user bỏ Twitter, khiến multiturn giảm 1.00 → 0.8333. Metric tổng tăng chưa đủ: mỗi giả thuyết cần theo dõi lỗi cũ lẫn lỗi mới, ưu tiên lượt cuối và chạy lại cùng bộ eval. Nguồn: [v0](../runs/v0_B_base_openrouter_20261110T102235938645.json), [v1](../runs/v1_B_base_openrouter_20261110T105423883723.json).

2. **Đặt quy ước tham số sát schema trong `tools.yaml`.** G03/G13 của [run 10 case](../runs/v2_B_group_openrouter_TranThaiHung_2A202603557_10cases.json) chọn đúng tool nhưng sai `sort_by`/thiếu `policy_area`: routing 1.00, argument 0.80. Prompt định nghĩa workflow/scope; declaration cần giải thích `submittedDate` so với `lastUpdatedDate`, khi dùng `source_citation` và điều kiện dùng/không dùng tool. Đây là hướng sửa tiếp theo, chưa được chứng minh bằng run v3. Contract test bảo đảm schema khớp code, chưa bảo đảm mô tả đủ rõ cho model.

3. **Routing đúng chưa đồng nghĩa hoàn thành tác vụ.** `run_eval.py` chấm lời gọi/args, không chấm toàn bộ `tool_results` hay chất lượng tóm tắt. Bug số byte trên Windows chỉ lộ khi unit test đọc file; với Telegram cần kiểm tra cả request lẫn nhánh không được gửi. Review thủ công vẫn cần cho nguồn trích dẫn, chất lượng báo cáo, xác nhận thực sự của người dùng và phản ứng của model trước injection. Kết hợp unit test, eval và đọc transcript để tránh kết luận vượt bằng chứng.

4. **Bằng chứng phải tái lập và gắn đúng artifact.** UI cho chọn v3 nhưng v2/v3 dùng chung file; transcript nhãn v0 cũng có thể được tạo sau khi prompt đã sửa. Cần đối chiếu `prompt_hash`, `tools_hash`, dataset và số case: 2/2 trên bộ nhỏ không thay thế 8/10 trên bộ đầy đủ. Tiếp theo cần snapshot riêng, chạy base/group v2/v3, ghi từng giả thuyết và metric vào version log, thêm negative eval cho export khi không được yêu cầu; giữ test offline và công khai bằng chứng còn thiếu.


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
