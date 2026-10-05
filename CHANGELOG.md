# Changelog

## 1.0.0 (2026-10-05)

- The Compost Bucket holds 3 times as much per fill by default: 450 instead of 150, about a 3x3 bed instead of 3 plots.
- Every watering can holds 3 times as much by default and keeps its tier: Wooden 600, Bronze 750, Steel 900, Adamant 1050, Rune 1200.
- `config.txt` sets the bucket and the cans separately, from 1 (vanilla) to 20.
- Pour rate is unchanged. Tooltips and fill bars read the new capacity from the same item data.
- Works on buckets and cans already in a bag. Adamant and Rune cans are picked up when their region's content loads.
- Logs any other container the game adds, unchanged, so a game update cannot silently leave one small.
