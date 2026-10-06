# Changelog

## 1.0.0 (2026-10-05)

The first release.

### Features

- The Compost Bucket holds 3 times as much per fill: 450 instead of 150. That's about a 3x3 bed instead of 3 plots.
- Every watering can holds 3 times as much and keeps its place in the tiers: Wooden 600, Bronze 750, Steel 900, Adamant 1050, Rune 1200.
- Containers still pour at their normal rate. Tooltips and fill bars show the new capacity.
- Buckets and cans already in your bag get the bigger capacity too.
- `config.txt` sets the bucket and the cans separately, from 1 (vanilla) to 20. Decimals work. A value that isn't a number falls back to 3, and one outside 1 to 20 is clamped.

### Technical notes

- Adamant and Rune cans are changed when their region's content loads.
- Any other container the game adds is logged and left unchanged, so a game update can't quietly leave one small.
