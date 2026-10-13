#!/usr/bin/env bash
# Regenerates Figs. 3, 4, 6-10 of the paper from data/figure_sources/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/figures_regenerated}"
python3 "$ROOT/analysis/make_figures.py" "$ROOT/data/figure_sources" "$OUT" 3d,4,6,7c,8,9,10h
cd "$OUT"
mv -f Fig3_ALT3_fig9style.pdf      Fig3.pdf
mv -f Fig4_R01_UPR_UER_PSV.pdf     Fig4.pdf
mv -f Fig6_IPFS_size_sweep.pdf     Fig6.pdf
mv -f Fig7_ALT2_two_scales.pdf     Fig7.pdf
mv -f Fig8_R10_S4_replay.pdf       Fig8.pdf
mv -f Fig9_R12_Qwen_flow_latency.pdf Fig9.pdf
mv -f Fig10H_Fabric_R11_P14.pdf    Fig10.pdf
rm -f *.png
echo "Figures written to $OUT"
