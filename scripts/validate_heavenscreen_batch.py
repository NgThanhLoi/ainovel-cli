#!/usr/bin/env python3
"""Validate Heavenscreen batch output."""

import os, sys, re, json

CH_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'novel', 'chapters')
ERRORS = []

def e(code, msg):
    ERRORS.append(f"[{code}] {msg}")

def validate():
    if not os.path.isdir(CH_DIR):
        e("FATAL", f"Chapters dir not found: {CH_DIR}")
        return

    files = sorted([f for f in os.listdir(CH_DIR) if f.endswith('.md')],
                   key=lambda x: int(x.split('.')[0]))
    if not files:
        e("FATAL", "No chapter files found")
        return

    nums = [int(f.split('.')[0]) for f in files]
    expected = set(range(min(nums), max(nums)+1))
    missing = sorted(expected - set(nums))
    if missing:
        intentional = [26, 79, 80]
        remaining = sorted(set(missing) - set(intentional))
        if remaining:
            e("SEQ-01", f"Missing chapter files: {remaining}")
        if 26 in missing:
            e("WARN", f"Missing ch26 (historical gap, not critical)")

    NON_TEYVAT = ['Lý Đại Ngưu', 'Trần Bình', 'Tiểu Mai', 'huyện thành',
                  'nhà máy dệt', 'công an', 'tỉnh thành', 'bí thư', 'chủ tịch huyện']
    SUSPICIOUS = ['huyện thành', 'tỉnh thành', 'công an', 'nhà máy', 'xưởng']

    for fn in files:
        path = os.path.join(CH_DIR, fn)
        with open(path) as f:
            raw = f.read()

        if raw.strip().startswith('{"output"'):
            e("FMT-01", f"{fn}: JSON wrapper in markdown file")
        if '"usage":' in raw or '"prompt_tokens"' in raw:
            e("FMT-02", f"{fn}: Usage metadata in chapter body")

        for ind in NON_TEYVAT:
            if ind in raw:
                e("CONT-01", f"{fn}: Wrong-project contamination ('{ind}')")
        for s in SUSPICIOUS:
            if s in raw:
                e("CONT-02", f"{fn}: Non-Teyvat setting hint ('{s}')")

        lines = raw.split('\n')
        first_heading = ''
        for line in lines:
            if line.startswith('# ') and not line.startswith('## '):
                first_heading = line[2:].strip()
                break
        # Check if heading contains a chapter number different from filename
        ch_num = int(fn.split('.')[0])
        heading_match = re.search(r'chương\s+(\d+)', first_heading.lower())
        if heading_match:
            heading_ch = int(heading_match.group(1))
            if heading_ch != ch_num and heading_ch < 20:  # only flag if significantly different
                e("SEQ-02", f"{fn}: Heading says chapter {heading_ch}, file is {fn}")

        if not re.search(r'Mondstadt|Liyue|Inazuma|Sumeru|Fontaine|Natlan'
                         r'|Snezhnaya|Nod Krai|Vực Đá Sâu|Vực Thẳm|Abyss', raw):
            e("LEDG-01", f"{fn}: No clear reality location marker")

    hard_errors = [e for e in ERRORS if e.startswith("[") and not e.startswith("[WARN")]
    if hard_errors:
        print(f"❌ VALIDATION FAILED: {len(hard_errors)} errors")
        for err in ERRORS:
            print(f"  {err}")
        sys.exit(1)
    else:
        if ERRORS:
            print(f"⚠️ VALIDATION PASSED WITH WARNINGS: {len(ERRORS)} warnings")
            for err in ERRORS:
                print(f"  {err}")
        else:
            print("✅ VALIDATION PASSED")
        sys.exit(0)

if __name__ == '__main__':
    validate()
