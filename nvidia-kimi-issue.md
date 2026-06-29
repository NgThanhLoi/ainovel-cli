# Vấn đề NVIDIA Kimi K2.6 — Báo cáo kỹ thuật

## Môi trường

- **Endpoint:** `http://localhost:20128/v1` (proxy tổng hợp)
- **Model ID:** `nvidia/moonshotai/kimi-k2.6`
- **Backend fingerprint:** `vllm-0.22.0-tp4-ep-ecc9852f`
- **Client:** litellm + agentcore (Go) qua OpenAI Chat Completions API

## Triệu chứng

### 1. Tool call streaming không chuẩn OpenAI (vLLM 0.22 legacy)

**So sánh format streaming:**

| Tiêu chí | NVIDIA Kimi (vLLM 0.22) | Tiêu chuẩn OpenAI |
|---|---|---|
| Tool call ID format | `functions.xxx:0` | `call_xxxxxxxxxxxx` |
| Content+tool_calls cùng chunk | ✅ Có (text bleed) | ❌ Không được phép |
| `tool_calls: []` trong content chunk | ✅ Có | ❌ Không |
| `reasoning_content` | ❌ Không | ✅ Có (tuỳ model) |
| finish_reason chunk riêng | ✅ Có | ✅ Có |

Ví dụ chunk có text bleed:
```json
{"choices": [{"delta": {"content": "Tôi sẽ gọi tool", "tool_calls": []}}]}
```
→ Client thấy `tool_calls: []` (empty) nên đánh dấu "không có tool call", sau đó tool call thật đến → client parse sai.

### 2. Inference quality: repetition drift (nghiêm trọng)

Khoảng **60-70% request** trả về text rác, không phải tool call:

**Kết quả thực tế:**
- Non-streaming, không tool: `"Hi there, friend!"` ✅ (0.5s)
- Non-streaming, có tool: `"Warn for brevity 2016 a heavy chunk take note on..."` ❌ (garbled)
- Finish reason: `"repetition"` — model tự detect lỗi và dừng
- Các request thành công xen kẽ thất bại (không consistent)

**Garbled text patterns:**
- Pha trộn Anh-Trung-Pháp vô nghĩa
- Ký tự Unicode lạ (`è üey éfo`)
- Lặp từ vô thức
- Model training bias: thiên về Chinese text ngay cả khi prompt tiếng Việt

### 3. So sánh cùng model, khác backend

| Route | Model ID | Backend | Quality | Tool call |
|---|---|---|---|---|
| `nvidia/...` | `nvidia/moonshotai/kimi-k2.6` | vLLM 0.22 | ❌ Garbled 60% | ❌ functions.xxx:0 |
| `cmc/...` | `cmc/moonshotai/Kimi-K2.6` | vLLM mới hơn? | ✅ Sạch, tiếng Việt | ✅ call_xxx |

CMC route dùng backend khác, output sạch, tool call chuẩn. Cùng model Kimi K2.6, khác inference stack.

## Nguyên nhân gốc rễ

1. **vLLM 0.22 cũ** không hỗ trợ streaming tool call theo OpenAI spec mới
2. **Repetition drift** do inference backend (có thể do quantization, sampling params, hoặc model sharding)
3. **Không fix được từ client** — prompt engineering và proxy không khắc phục được inference quality issue

## Đã thử nhưng không hiệu quả

- Prompt engineering: "CHỈ tool, KHÔNG text" → vẫn ra text rác
- Proxy Python: convert SSE → non-streaming → fix ID → vẫn silent fail vì model không sinh tool call
- `parallel_tool_calls: false` → không ảnh hưởng
- `stream_options: {include_usage: false}` → không ảnh hưởng
- `extra_body` params → không ảnh hưởng
