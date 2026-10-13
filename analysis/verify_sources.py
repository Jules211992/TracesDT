#!/usr/bin/env python3
"""Checks the SHA-256 of every figure source file against FILES_SHA256_PROVENANCE.csv."""
import csv, hashlib, sys
from pathlib import Path

base = Path(__file__).resolve().parents[1] / "data" / "figure_sources"
ok = bad = 0
for row in csv.DictReader(open(base / "FILES_SHA256_PROVENANCE.csv")):
    f = base / row["path"].removeprefix("DATA/")
    if not f.exists():
        print("MISSING ", row["path"]); bad += 1; continue
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    if h == row["sha256"]:
        ok += 1
    else:
        print("MISMATCH", row["path"]); bad += 1
print(f"{ok} files verified, {bad} problems")
sys.exit(1 if bad else 0)
