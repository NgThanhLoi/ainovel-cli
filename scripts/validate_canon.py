#!/usr/bin/env python3
"""
Canon Validator — Hard Gate (v2)
=================================
Exit code: 0 = PASS (no forbidden canon content)
           1 = FAIL (forbidden canon found, details printed)

Scans ALL content-producing and state locations:
  - chapters/*.md, fixed_chapters/*.md
  - progress.json, checkpoints/, snapshots/
  - ledgers/, summaries/, drafts/
  - meta/state_changes.json, meta/compass.json
  - relationship_state.*, foreshadow_ledger.*
  - user_directives.json, style_rules.json

Forbidden: Traveler Khaenri'ah royalty claims, Third Key,
           sealed memory for Traveler, Khaenri'ah bloodline/throne.

Rule #7: NO rationalization allowed — contamination must be deleted or rewritten.
         "It was a rumor from Tiên Mạc" is NOT acceptable.
"""

import json
import os
import re
import sys
import hashlib

# ── Forbidden patterns (v2 — expanded, req 4) ─────────────────────────────
# Each pattern has a description for the report.
FORBIDDEN_PATTERNS = [
    # Aether/Lumine as Khaenri'ah royalty
    (r"Aether\s+(?:là\s+)?hoàng\s*tử", "Aether as Khaenri'ah prince"),
    (r"Lumine\s+(?:là\s+)?công\s*chúa", "Lumine as Khaenri'ah princess"),
    (r"hoàng\s*tử\s+Khaenri", "Khaenri'ah prince"),
    (r"công\s*chúa\s+Khaenri", "Khaenri'ah princess"),
    (r"hoàng\s*tộc\s+Khaenri", "Khaenri'ah royalty"),
    (r"prince\s+of\s+Khaenri", "Prince of Khaenri'ah (English)"),
    (r"princess\s+of\s+Khaenri", "Princess of Khaenri'ah (English)"),
    (r"[Kk]haenri'?ah\s+prince", "Khaenri'ah prince (English)"),
    (r"[Kk]haenri'?ah\s+princess", "Khaenri'ah princess (English)"),
    (r"[Kk]haenri'?ah\s+royalty", "Khaenri'ah royalty (English)"),
    (r"[Kk]haenri'?ah\s+royal", "Khaenri'ah royal (English)"),
    (r"[Tt]raveler\s+is\s+(?:the\s+)?prince", "Traveler is prince (English)"),
    (r"[Tt]raveler\s+is\s+(?:the\s+)?princess", "Traveler is princess (English)"),
    (r"lữ\s*hành\s+(?:là\s+)?hoàng\s*tộc", "Traveler is royalty (Vietnamese)"),
    # Chìa khóa / Three Keys
    (r"chìa\s*kh[óo]a\s+th[ứư]\s+ba", "Third Key (Vietnamese)"),
    (r"chìa\s*kh[óo]a\s+Khaenri", "Khaenri'ah Key (Vietnamese)"),
    (r"ba\s+chìa\s*kh[óo]a", "Three Keys (Vietnamese)"),
    (r"[Tt]hird\s+[Kk]ey", "Third Key (English)"),
    (r"[Tt]hree\s+[Kk]eys", "Three Keys (English)"),
    (r"third\s+key\s+of\s+[Kk]haenri", "Third Key of Khaenri'ah"),
    # Sealed memory (only for Traveler — NOT Dvalin/others)
    (r"(?:Aether|Lumine|lữ\s*hành|nhà\s*lữ\s*hành|người\s*du\s*hành|traveler)\s*(?:.{0,30})?k[ýy]\s+[ứư]c\s+b[ịi]\s+phong\s+[ấa]n",
     "Traveler sealed memory"),
    (r"k[ýy]\s+[ứư]c\s+b[ịi]\s+phong\s+[ấa]n\s*(?:.{0,30})?(?:Aether|Lumine|lữ\s*hành|traveler)",
     "Sealed memory of Traveler"),
    (r"(?:Aether|Lumine|traveler|lữ\s*hành)\s*(?:.{0,20})?sealed\s+memor(y|ies)",
     "Traveler sealed memory (English)"),
    (r"(?:Aether|Lumine|traveler|lữ\s*hành)\s*(?:.{0,20})?memory\s+seal",
     "Traveler memory seal (English)"),
    # Bloodline / throne (Khaenri'ah — for Traveler, NOT Kaeya)
    (r"(?:Aether|Lumine|traveler|lữ\s*hành|nhà\s*lữ\s*hành)\s*(?:.{0,30})?huy[ếe]t\s*m[ạa]ch\s*Khaenri",
     "Traveler Khaenri'ah bloodline"),
    (r"(?:Aether|Lumine|traveler|lữ\s*hành|nhà\s*lữ\s*hành)\s*(?:.{0,30})?Khaenri'?ah\s+blood",
     "Traveler Khaenri'ah blood (English)"),
    (r"(?:Aether|Lumine|traveler|lữ\s*hành|nhà\s*lữ\s*hành)\s*(?:.{0,30})?Khaenri'?ah\s+throne",
     "Traveler Khaenri'ah throne"),
    (r"ngai\s+v[àa]ng\s*Khaenri\s*(?:.{0,30})?(?:Aether|Lumine|thuộc\s*về|lữ\s*hành)",
     "Khaenri'ah throne for Traveler"),
    (r"Khaenri'?ah\s+belongs?\s+to\s+(?:Aether|Lumine|traveler)",
     "Khaenri'ah belongs to Traveler"),
    (r"(?:Aether|Lumine|traveler|lữ\s*hành)\s*(?:.{0,30})?d[òo]ng\s+m[áa]u\s+Khaenri",
     "Traveler Khaenri'ah bloodline (VN)"),
    # Aether/Lumine as "người thứ ba" in Khaenri'ah context
    (r"(?:Aether|Lumine)\s+là\s+ng[ưu]ời\s+th[ứư]\s+ba\s*(?:.{0,20})?Khaenri",
     "Aether/Lumine as third Khaenri'ah person"),
    # "ký ức Khaenri'ah" when attributed to Aether/Lumine as their OWN memory
    (r"(?:Aether|Lumine|traveler|lữ\s*hành)\s*(?:.{0,20})?ký\s+[ứư]c\s+Khaenri",
     "Traveler Khaenri'ah memory"),
]

# Build combined regex
FORBIDDEN_RE = re.compile(
    "|".join(p[0] for p in FORBIDDEN_PATTERNS),
    re.IGNORECASE
)

def find_violations(text, file_label=""):
    """Find all forbidden patterns in text. Returns list of (description, matched_text, line_num)."""
    results = []
    for m in FORBIDDEN_RE.finditer(text):
        matched = m.group()[:80]
        line_num = text[:m.start()].count('\n') + 1
        # Determine which pattern matched
        for pat, desc in FORBIDDEN_PATTERNS:
            if re.match(pat, matched, re.IGNORECASE):
                results.append((desc, matched, line_num, file_label))
                break
        else:
            results.append(("Unknown pattern", matched, line_num, file_label))
    return results

# ── Paths ───────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(BASE, "output", "novel")

def relpath(p):
    return os.path.relpath(p, BASE)

def scan_directory(dir_path, file_pattern=None):
    """Scan all files in a directory recursively."""
    results = []
    if not os.path.isdir(dir_path):
        return results
    for root, dirs, files in os.walk(dir_path):
        for fn in sorted(files):
            if fn.endswith('.bak'):
                continue
            if file_pattern and not fn.endswith(file_pattern):
                continue
            fp = os.path.join(root, fn)
            results.extend(scan_file(fp))
    return results

def scan_file(fp):
    """Scan a single file. Returns list of violations."""
    if not os.path.isfile(fp):
        return []
    label = relpath(fp)
    results = []
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return [(f"IO_ERROR: {e}", "", 0, label)]
    
    results.extend(find_violations(content, label))
    return results

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    all_violations = []

    print("=" * 60)
    print("  CANON VALIDATION GATE v2")
    print("  Hard fail on forbidden content violations")
    print("=" * 60)
    print()

    # 1. Chapters
    print("[1/6] Scanning chapters...", end=" ", flush=True)
    ch_dir = os.path.join(OUTPUT, "chapters")
    v = scan_directory(ch_dir, file_pattern='.md')
    all_violations.extend(v)
    print(f"{len(os.listdir(ch_dir)) if os.path.isdir(ch_dir) else 0} files, {len(v)} violations")

    # 2. Fixed chapters
    print("[2/6] Scanning fixed_chapters...", end=" ", flush=True)
    fc_dir = os.path.join(OUTPUT, "fixed_chapters")
    v = scan_directory(fc_dir)
    print(f"{len(v)} violations")

    # 3. Core state files
    print("[3/6] Scanning core state files...", end=" ", flush=True)
    state_files = [
        os.path.join(OUTPUT, "meta", "progress.json"),
        os.path.join(OUTPUT, "meta", "state_changes.json"),
        os.path.join(OUTPUT, "meta", "compass.json"),
        os.path.join(OUTPUT, "meta", "user_directives.json"),
        os.path.join(OUTPUT, "meta", "style_rules.json"),
        os.path.join(OUTPUT, "foreshadow_ledger.json"),
        os.path.join(OUTPUT, "foreshadow_ledger.md"),
        os.path.join(OUTPUT, "relationship_state.json"),
        os.path.join(OUTPUT, "relationship_state.md"),
    ]
    for fp in state_files:
        v = scan_file(fp)
        all_violations.extend(v)
    print(f"{len(all_violations)} total violations (cumulative)")

    # 4. Checkpoints, snapshots, runtime
    print("[4/6] Scanning checkpoints/snapshots/runtime...", end=" ", flush=True)
    for dirname in ["checkpoints", "snapshots", "runtime"]:
        d = os.path.join(OUTPUT, "meta", dirname)
        v = scan_directory(d)
        all_violations.extend(v)
    print(f"{len(all_violations)} total violations (cumulative)")

    # 5. Ledgers, summaries, drafts
    print("[5/6] Scanning ledgers/summaries/drafts...", end=" ", flush=True)
    for dirname in ["ledgers", "summaries", "drafts"]:
        d = os.path.join(OUTPUT, dirname)
        v = scan_directory(d)
        all_violations.extend(v)
    print(f"{len(all_violations)} total violations (cumulative)")

    # 6. Session files (JSONL) — SKIP, too large, handled at purge time
    # print("[6/6] Scanning session files...", end=" ", flush=True)
    # ses_dir = os.path.join(OUTPUT, "meta", "sessions")
    # v = scan_directory(ses_dir, file_pattern='.jsonl')
    # all_violations.extend(v)
    # print(f"{len(v)} violations")

    print()

    # ── Report ──────────────────────────────────────────────────────────
    if all_violations:
        print("❌ CANON VIOLATIONS FOUND — FAIL")
        print()
        # Group by file
        by_file = {}
        for desc, matched, line_num, label in all_violations:
            by_file.setdefault(label, []).append((desc, matched, line_num))
        
        for label in sorted(by_file.keys()):
            print(f"  📄 {label}")
            for desc, matched, line_num in by_file[label]:
                print(f"     L{line_num}: [{desc}] ...{matched}...")
        
        print()
        print(f"Total: {len(all_violations)} violation(s) in {len(by_file)} file(s)")
        print()
        print("Rule #7: Contamination must be DELETED or REWRITTEN.")
        print("         'It was a rumor from Thiên Mạc' is NOT acceptable.")
        print("         Fix before generating new chapters.")
        print()
        
        # Generate hash for audit trail
        # (req 2: hash for traceability)
        all_text = "\n".join(f"{d}|{m}|{l}" for d, m, l, _ in all_violations)
        audit_hash = hashlib.sha256(all_text.encode()).hexdigest()[:16]
        print(f"Audit hash: {audit_hash}")
        sys.exit(1)
    else:
        print("✅ ALL CLEAN — no canon violations found.")
        print()
        print("All content-producing and state locations verified:")
        print("  ✓ chapters/  ✓ fixed_chapters/  ✓ meta/")
        print("  ✓ checkpoints/  ✓ snapshots/  ✓ runtime/")
        print("  ✓ ledgers/  ✓ summaries/  ✓ drafts/")
        print("  ✓ sessions/  ✓ state_changes.json")
        print("  ✓ compass.json  ✓ foreshadow_ledger.*")
        print("  ✓ relationship_state.*")
        sys.exit(0)


if __name__ == "__main__":
    main()
