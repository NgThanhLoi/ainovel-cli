# Pipeline Fix Report

## Các vấn đề đã fix

### 1. JSON Wrapper Export Bug
- **Vấn đề:** Coordinator/exporter ghi raw JSON response vào file .md
- **Fix:** unwrap 32 files, xoá `{"output":"...` wrapper
- **Prevention:** Validation script `scripts/validate_heavenscreen_batch.py` sẽ reject nếu file bắt đầu bằng `{"output"`

### 2. Wrong-project Contamination
- **Vấn đề:** AI trained data lẫn project khác (Lý Đại Ngưu story)
- **Fix:** Archive ch79, 80 vào `chapters_rejected/`
- **Prevention:** Validation script kiểm tra non-Teyvat indicators, coordinator addendum cấm OC/world ngoài Teyvat

### 3. Non-canon Khaenri'ah Lore
- **Vấn đề:** Ch84 viết Aether là hoàng tộc Khaenri'ah — sai canon
- **Fix:** Rewrite toàn bộ ch84 (Aether là lữ khách từ thế giới khác, đúng canon)
- **Prevention:** Canon safeguards cập nhật rule rõ về Aether/Lumine nguồn gốc

### 4. Thiếu Ledger
- **Vấn đề:** Không có world-state, reveal, video usage, relationship, faction ledgers
- **Fix:** Tạo 5 ledgers mới
- **Prevention:** Coordinator addendum yêu cầu đọc ledger trước và cập nhật sau mỗi chapter

### 5. Thiếu Validation
- **Vấn đề:** Không có cơ chế validate output trước khi commit
- **Fix:** Tạo `scripts/validate_heavenscreen_batch.py` — fail non-zero nếu lỗi

### 6. Prompt Addendums
- **Vấn đề:** Architect/Coordinator/Writer không có hướng dẫn specific cho heavenscreen
- **Fix:** Tạo 3 prompt addendums

## Files đã tạo/sửa

### Mới
- `scripts/validate_heavenscreen_batch.py` — validation script
- `ledgers/world_state_ledger.yaml`
- `ledgers/reveal_ledger.yaml`
- `ledgers/video_usage_ledger.yaml`
- `ledgers/relationship_reaction_ledger.yaml`
- `ledgers/faction_action_ledger.yaml`
- `prompts/architect_addendum_heavenscreen.md`
- `prompts/coordinator_addendum_heavenscreen.md`
- `prompts/writer_addendum_heavenscreen.md`
- `reports/heavenscreen_batch_audit.md`
- `reports/heavenscreen_pipeline_fix_report.md`

### Sửa
- `assets/prompts/canon-safeguards.md` — thêm Aether/Lumine nguồn gốc canon
- 32 chapter files — unwrap JSON wrapper
- Chương 84 — rewrite đúng canon

### Archive
- `chapters_rejected/79.md`
- `chapters_rejected/80.md`

## Khuyến nghị
1. Chạy validation script sau mỗi batch: `python3 scripts/validate_heavenscreen_batch.py`
2. Coordinator phải đọc ledger trước khi plan chapter
3. Test batch tiếp theo: chương 1-10 với setup mới
4. Không chạy 500 chương một lần
