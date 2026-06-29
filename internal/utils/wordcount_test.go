package utils

import (
	"strings"
	"testing"
)

func TestCountVietnameseWords(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{
			name:     "basic_vietnamese",
			input:    "Tôi yêu Việt Nam",
			expected: 4,
		},
		{
			name:     "with_punctuation",
			input:    "Tôi yêu Việt Nam! Anh ấy đã đến, rồi đi.",
			expected: 10,
		},
		{
			name:     "punctuation_only",
			input:    "!!! ??? ... ,.",
			expected: 0,
		},
		{
			name:     "numbers_only",
			input:    "123 456 789",
			expected: 0,
		},
		{
			name:     "mixed_numbers_and_letters",
			input:    "Chương 1: Mở đầu",
			expected: 3, // Chương, Mở, đầu — '1:' không có chữ cái
		},
		{
			name:     "markdown_bold",
			input:    "Tôi yêu **Việt Nam**",
			expected: 4, // Tôi, yêu, Việt, Nam (sau strip bold)
		},
		{
			name:     "markdown_heading",
			input:    "## Chương 1\nNội dung chương",
			expected: 4, // Chương, Nội, dung, chương (1: bỏ)
		},
		{
			name:     "markdown_italic",
			input:    "Anh ấy *rất* đẹp trai",
			expected: 5, // Anh, ấy, rất, đẹp, trai
		},
		{
			name:     "markdown_strikethrough",
			input:    "Cô ấy ~~không~~ thích",
			expected: 4, // Cô, ấy, không, thích
		},
		{
			name:     "markdown_inline_code",
			input:    "Gọi `fmt.Println()` để in",
			expected: 4, // Gọi, fmt.Println(), để, in
		},
		{
			name:     "markdown_link",
			input:    "Xem thêm [tại đây](https://example.com)",
			expected: 4, // Xem, thêm, tại, đây
		},
		{
			name:     "markdown_full_chapter",
			input:    "## Chương 1: **Khởi đầu**\n\nTrời hôm nay *rất* đẹp. Tôi ~~chợt~~ nhận ra mình `đang` mơ.\n\nXem [link](url) để biết thêm.",
			expected: 20, // Chương, Khởi, đầu, Trời, hôm, nay, rất, đẹp., Tôi, chợt, nhận, ra, mình, đang, mơ., Xem, link, để, biết, thêm.
		},
		{
			name:     "empty_string",
			input:    "",
			expected: 0,
		},
		{
			name:     "whitespace_only",
			input:    "   \n\n\t  ",
			expected: 0,
		},
		{
			name:     "chinese_chars_no_spaces",
			input:    strings.Repeat("汉", 2500),
			expected: 1, // 2500 Chinese chars, no spaces → 1 token
		},
		{
			name:     "vietnamese_paragraph",
			input:    "Hôm nay trời đẹp quá. Tôi muốn đi dạo trong công viên và hít thở không khí trong lành.",
			expected: 19, // Đếm từng từ cách nhau bởi space
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CountVietnameseWords(tt.input)
			if got != tt.expected {
				t.Errorf("CountVietnameseWords(%q) = %d, want %d", tt.input, got, tt.expected)
			}
		})
	}
}

func TestCountVietnameseWords_NotRuneCount(t *testing.T) {
	// Xác nhận KHÔNG phải đếm rune
	text := "Tôi yêu Việt Nam"
	runeCount := len([]rune(text))
	wordCount := CountVietnameseWords(text)

	if wordCount == runeCount {
		t.Errorf("wordCount == runeCount (%d), chứng tỏ vẫn đang đếm ký tự!", wordCount)
	}
	t.Logf("OK: runeCount=%d, wordCount=%d (khác nhau như mong đợi)", runeCount, wordCount)
}

func TestCountVietnameseWords_LongText(t *testing.T) {
	// Test với 5000 từ tiếng Việt (cách nhau bởi space)
	words := make([]string, 5000)
	for i := range words {
		words[i] = "tôi"
	}
	text := strings.Join(words, " ")
	got := CountVietnameseWords(text)
	if got != 5000 {
		t.Errorf("5000 words = %d, want 5000", got)
	}
}
