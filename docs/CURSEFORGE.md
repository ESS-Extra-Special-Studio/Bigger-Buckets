# CurseForge page draft: Bigger Buckets

Draft text for the CurseForge project page. No project exists yet; links are added only once real URLs exist.

## Project

- **Name:** Bigger Buckets
- **Summary (one line):** The Compost Bucket and every watering can hold 3 times as much per fill (configurable).
- **Category:** Gameplay / Quality of Life
- **Game version:** Steam build 25632050
- **Licence:** see LICENSE in the zip

## Description

Three plots per bucket is kinda wild. Bigger Buckets makes the Compost Bucket and every watering can hold more per fill, so one trip to the composter or the water covers a whole bed.

| Container | Vanilla | Bigger Buckets (x3) |
|-----------|--------:|--------------------:|
| Compost Bucket | 150 | 450 |
| Wooden Watering Can | 200 | 600 |
| Bronze Watering Can | 250 | 750 |
| Steel Watering Can | 300 | 900 |
| Adamant Watering Can | 350 | 1050 |
| Rune Watering Can | 400 | 1200 |

Nothing else changes: each container pours at its normal rate, the tiers keep their order, and tooltips and fill bars show the bigger capacity. Plot counts per fill are approximate; the game doesn't show the per-plot amount.

**Settings.** `BiggerBuckets\config.txt` sets the bucket and the cans separately, from 1 (vanilla) to 20; decimals work. Restart the game after editing.

**Multiplayer.** Everyone in the world should use the same settings; the host's copy most likely decides how much a fill holds.

**Other mods.** Stacks with pak mods that change capacity (such as GreaterFarmingTools); set the matching value to 1 if you only want the other mod's numbers.

### Install

1. Install UE4SS for RuneScape: Dragonwilds (3.0.1, the "UE4SS Steam (latest)" build).
2. Install Bigger Buckets. The CurseForge app puts it in `RSDragonwilds\Content\Paks\~mods\BiggerBuckets`.

## Relations

- **Required:** none on CurseForge. Bigger Buckets does not need ESL:DragonWilds or any other Extra Special Studio mod. UE4SS is installed separately (see Install).

## Lore and affiliation

No lore: Bigger Buckets only changes numbers.

Bigger Buckets is a fan project by Extra Special Studio. It is not affiliated with, endorsed by, or sponsored by Jagex Ltd. RuneScape and RuneScape: Dragonwilds are trademarks of Jagex Ltd.

## Screenshots

None captured yet. Needed:

1. A Compost Bucket tooltip showing 450.
2. A watering can tooltip showing its x3 capacity.
3. A 3x3 bed composted from one fill (also confirms the plots-per-fill claim).
4. `config.txt` open in a text editor.
