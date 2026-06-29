# Heavenscreen Batch Audit Report

## Thông tin
- **Repo:** /projects/ainovel-cli
- **Batch:** chương 1-84 (83 files)
- **Audit date:** 2026-06-29

## Tổng quan

| Hạng mục | Số lượng |
|---|---|
| Tổng file | 83 (ch1-ch84, thiếu ch26) |
| File JSON wrapper | **32** (đã fix) |
| File contamination | **2** (ch79, 80 — đã archive) |
| File sạch sau fix | **81** |
| Wrong-project indicators | Lý Đại Ngưu, Trần Bình, Tiểu Mai, huyện thành, nhà máy dệt, công an |

## Chi tiết lỗi

### 1. JSON Wrapper (FMT-01)
32 files chứa `{"output":"...` wrapper thay vì pure markdown.
- **Nguyên nhân:** Exporter ghi raw response từ coordinator mà không unwrap output field.
- **Fix:** Đã unwrap toàn bộ 32 files.
- **File ảnh hưởng:** ch16, 21, 25, 28, 30, 31, 33-37, 40-48, 50-57, 64, 65, 71, 79

### 2. Wrong-project Contamination (CONT-01)
Chương 79 và 80 chứa toàn bộ cast/world không thuộc Teyvat:
- Nhân vật: Lý Đại Ngưu, Trần Bình, Tiểu Mai
- Địa điểm: Nam thôn, huyện thành, nhà máy dệt
- Bối cảnh: công an, tỉnh thành, chủ tịch huyện
- **Mức độ:** Nghiêm trọng — toàn bộ chapter là project khác
- **Fix:** Đã archive vào `chapters_rejected/`. Không dùng làm context.

### 3. Missing Chapter Numbers (SEQ-01)
- Thiếu chương 26 (không rõ nguyên nhân — có thể do lỗi commit trước đó)

### 4. Reality Route
- Reality Arc di chuyển đúng: Mondstadt (ch1-27) → Liyue (ch28-58) → Inazuma (59-78+)
- Không phát hiện route jump không giải thích

### 5. Future Reveal
- Chương 84 cũ chứa non-canon Khaenri'ah royalty plot — đã rewrite
- Các reveal khác trong ngưỡng cho phép

### 6. Tone
- Phát hiện một số chương Liyue có tone streak lore_hint hơi dài (không quá ngưỡng 3)

## Kết luận
- **Giữ:** 81 chapters (ch1-84 trừ 26, 79, 80)
- **Archive:** ch26 (missing), ch79, 80 (wrong-project)
- **Rewrite sẵn:** ch84 (non-canon lore)
- **Cần regenerate:** Không — 81 chapters đủ cho audit hiện tại
