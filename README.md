# Bigger Buckets

A small RuneScape: Dragonwilds mod from Extra Special Studio. The Compost Bucket and every watering can hold more per fill, so one trip to the composter or the water covers a whole bed instead of three plots.

Nothing else changes. Each container still pours at its normal rate, the tiers keep their order, and the bucket's tooltip and fill bar use the bigger capacity because the game reads it from the same item data.

## What it changes

Default: everything holds 3 times as much.

| Container | Vanilla | Bigger Buckets (x3) |
|-----------|--------:|--------------------:|
| Compost Bucket | 150 | 450 |
| Wooden Watering Can | 200 | 600 |
| Bronze Watering Can | 250 | 750 |
| Steel Watering Can | 300 | 900 |
| Adamant Watering Can | 350 | 1050 |
| Rune Watering Can | 400 | 1200 |

Vanilla numbers are the `Capacity` values in the game's own item data for Steam build 25632050.

Players count about 3 plots per Compost Bucket fill, which makes a plot about 50 compost. At x3 the bucket covers about 9 plots, a whole 3x3 bed. The watering cans scale the same way. The game does not show the per-plot amount, so treat plot counts as approximate.

## Settings

Open `BiggerBuckets\config.txt`:

```
compost_bucket = 3
watering_cans = 3
```

Each number multiplies how much that container holds. `1` is vanilla, the allowed range is 1 to 20, and decimals such as `2.5` work. Restart the game after editing. A missing setting uses 3. A value that isn't a number also uses 3, and a number outside 1 to 20 is clamped to the nearest end; both are noted in the log.

## Requirements

- RuneScape: Dragonwilds on Steam
- UE4SS for RuneScape: Dragonwilds

Bigger Buckets does not need any other Extra Special Studio mod.

## Install

The CurseForge app installs Dragonwilds mods into:

`RSDragonwilds\RSDragonwilds\Content\Paks\~mods`

Bigger Buckets is the `BiggerBuckets` folder in there. If your UE4SS only loads Lua mods from `RSDragonwilds\Binaries\Win64\ue4ss\Mods`, put the folder there instead.

To check that it loaded, look in `RSDragonwilds\Binaries\Win64\ue4ss\UE4SS.log` for:

`[Bigger Buckets] Loaded 1.0.0`

followed by one `Capacity 150 -> 450` style line per container a few seconds later, at the main menu.

## Multiplayer

Everyone in the world should install it with the same settings. Watering is applied by the host, so the host's copy most likely decides how much a fill holds. Each player's own copy decides what their tooltip and fill bar say. If only some players have it, the numbers they see may not match what actually pours.

## Other mods

Bigger Buckets multiplies whatever capacity the item has when it loads. A pak mod that also changes container capacity, such as GreaterFarmingTools, stacks with it: its 300 compost bucket becomes 900 at x3. Set the matching value to `1` if you only want the other mod's numbers.

## Uninstalling

Delete the `BiggerBuckets` folder. Saved buckets and cans keep their contents. A container filled above its vanilla capacity has not been tested after removal, so empty or use up big fills first.

## Licence

See [LICENSE](LICENSE). Not affiliated with Jagex.
