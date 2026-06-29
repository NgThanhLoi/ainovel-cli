#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra số từ tiếng Việt của các chương.
Đếm từ (word) tiếng Việt - token phân cách bởi whitespace, không tính dấu câu.
"""

import re
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def count_vietnamese_words(text: str) -> int:
    """Đếm số từ tiếng Việt (loại bỏ định dạng Markdown, chỉ tính token có chữ cái)"""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    tokens = text.split()
    count = 0
    for tok in tokens:
        for ch in tok:
            if ch.isalpha():
                count += 1
                break
    return count


def extract_content_from_chapter(file_path: Path) -> str:
    """Trích xuất nội dung chính từ file chương (loại bỏ tiêu đề metadata)"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    content_start = 0
    for i, line in enumerate(lines):
        if line.startswith('#') and 'Chương' in line:
            content_start = i + 1
            break

    return '\n'.join(lines[content_start:])


def check_chapter(file_path: str, min_words: int = 3000) -> dict:
    """检查单个章节的字数"""
    path = Path(file_path)
    if not path.exists():
        return {
            'file': str(path),
            'exists': False,
            'word_count': 0,
            'status': 'error',
            'message': f'文件不存在: {file_path}',
        }

    main_content = extract_content_from_chapter(path)
    word_count = count_vietnamese_words(main_content)
    status = 'pass' if word_count >= min_words else 'fail'
    message = f'Số từ: {word_count}'
    if word_count >= min_words:
        message += ' (✓ đạt)'
    else:
        message += f' (✗ thiếu, cần tối thiểu {min_words} từ)'

    return {
        'file': str(path),
        'exists': True,
        'word_count': word_count,
        'status': status,
        'message': message,
    }


def check_all_chapters(directory: str, pattern: str = '第*.md', min_words: int = 3000) -> list:
    """检查目录下所有符合模式的章节文件"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f'错误: 目录不存在 - {directory}')
        return []

    chapter_files = sorted(dir_path.glob(pattern))
    return [check_chapter(str(chapter_file), min_words) for chapter_file in chapter_files]


def print_results(results: list, min_words: int = 3000) -> None:
    """In kết quả kiểm tra"""
    if not results:
        print('Không tìm thấy file chương nào')
        return

    total_words = 0
    passed = 0
    failed = 0

    print('\n' + '=' * 60)
    print('BÁO CÁO KIỂM TRA SỐ TỪ')
    print('=' * 60)

    for result in results:
        if not result['exists']:
            print(f'\n❌ {result["file"]}')
            print(f'   {result["message"]}')
            continue

        total_words += result['word_count']
        if result['status'] == 'pass':
            passed += 1
            icon = '✅'
        else:
            failed += 1
            icon = '⚠️ '

        print(f'\n{icon} {Path(result["file"]).name}')
        print(f'   {result["message"]}')

    print('\n' + '-' * 60)
    print(f'Tổng: {len(results)} chương | {passed} chương đạt | {failed} chương thiếu | Tổng số từ: {total_words:,}')
    print('-' * 60)

    if failed > 0:
        print(f'\n⚠️  Có {failed} chương chưa đủ {min_words} từ, gợi ý mở rộng:')
        print('   - Thêm miêu tả chi tiết (môi trường, tâm lý, hành động)')
        print('   - Tăng cường đối thoại')
        print('   - Mở rộng nội tâm nhân vật')
        print('   - Bổ sung bối cảnh cốt truyện')
        print('\n   Tham khảo: references/content-expansion.md')


def main() -> None:
    """Hàm chính"""
    if len(sys.argv) < 2:
        print('Cách dùng:')
        print('  Kiểm tra một chương: python check_chapter_wordcount.py <đường-dẫn-file> [số-từ-tối-thiểu]')
        print('  Kiểm tra tất cả:     python check_chapter_wordcount.py --all <đường-dẫn-thư-mục> [số-từ-tối-thiểu]')
        print('')
        print('Ví dụ:')
        print('  python check_chapter_wordcount.py novels/Chương01.md')
        print('  python check_chapter_wordcount.py novels/Chương01.md 3500')
        print('  python check_chapter_wordcount.py --all novels/')
        print('  python check_chapter_wordcount.py --all novels/ 3500')
        return

    if sys.argv[1] == '--all':
        if len(sys.argv) < 3:
            print('Lỗi: cần đường dẫn thư mục khi dùng --all')
            return
        directory = sys.argv[2]
        min_words = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
        results = check_all_chapters(directory, min_words=min_words)
        print_results(results, min_words)
        return

    file_path = sys.argv[1]
    min_words = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    result = check_chapter(file_path, min_words)
    print_results([result], min_words)


if __name__ == '__main__':
    main()
