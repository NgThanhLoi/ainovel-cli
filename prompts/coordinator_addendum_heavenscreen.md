# Coordinator Addendum — Heavenscreen What-if

## Trước mỗi chapter
1. Đọc world_state_ledger.yaml (vị trí hiện tại, task đang làm)
2. Đọc reveal_ledger.yaml (đã reveal gì, còn gì bị lock)
3. Đọc video_usage_ledger.yaml (video nào đã dùng)
4. Đọc faction_action_ledger.yaml (các phe đang làm gì)
5. Kiểm tra tone streak (không quá 3 chương nặng liên tiếp)
6. Kiểm tra future_reveal_count (tối đa 2)

## Sau mỗi chapter
1. Cập nhật world_state_ledger.yaml
2. Cập nhật reveal_ledger.yaml nếu có reveal mới
3. Cập nhật video_usage_ledger.yaml
4. Cập nhật relationship_reaction_ledger.yaml
5. Cập nhật faction_action_ledger.yaml

## Hard Guards — vi phạm thì reject/rewrite
- Không để reality location nhảy không có travel_transition
- Không để duplicate video không khai báo replay/remix
- Không để future_reveal_count >= 3
- Không để tone streak nặng quá 3
- Không canon hóa Traveler ship
- Không dùng corrupt/rejected chapters làm context
- Không mở non-Teyvat long-form arc không registered
- Không để wrong-project contamination lọt vào

## Video Library trạng thái
- Mỗi screen_video_id chỉ dùng 1 lần, trừ khi có flag replay/remix/follow_up
- Kiểm tra video_usage_ledger.yaml trước khi chọn video mới
