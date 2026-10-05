"""Static check for Bigger Buckets: compiles the Lua with Lua 5.4 and runs
main.lua against a mocked UE4SS API (fake container assets with the vanilla
values read from the cooked data). Proves syntax and logic only; it says
nothing about the real game. Needs the lupa package.

Usage: python check_lua.py
"""
import os
import shutil
import sys
import tempfile

from lupa import lua54

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(REPO, "BiggerBuckets")

VANILLA = {
    "ITEM_Bucket_Compost": (150, 10),
    "ITEM_WateringCan_Wood": (200, 10),
    "ITEM_WateringCan_Bronze": (250, 25),
    "ITEM_WateringCan_Steel": (300, 25),
    "ITEM_WateringCan_Adamant": (350, 40),
    "ITEM_WateringCan_Rune": (400, 40),
}

MOCK = r"""
local logs, loops, objects, loaded = {}, {}, {}, {}
print = function(s) logs[#logs + 1] = (tostring(s):gsub("\n$", "")) end
LoopAsync = function(ms, fn) loops[#loops + 1] = fn end
ExecuteInGameThread = function(fn) fn() end
local function make(name, cap, per)
    local o = { Capacity = cap, AmountDischargedPerUse = per, PlotDischargeMultiplier = 1.0, _name = name }
    function o:IsValid() return true end
    function o:GetFName() return { ToString = function() return name end } end
    return o
end
StaticFindObject = function(path)
    local name = path:match("%.([^%.]+)$")
    if loaded[name] then return objects[name] end
    return nil
end
FindAllOf = function(cls)
    local out = {}
    for name, o in pairs(objects) do if loaded[name] then out[#out + 1] = o end end
    return out
end
return {
    logs = logs, loops = loops, objects = objects, loaded = loaded, make = make,
    tick = function() for _, fn in ipairs(loops) do fn() end end,
}
"""


def run_case(title, config_text, steps):
    tmp = tempfile.mkdtemp()
    try:
        mod = os.path.join(tmp, "BiggerBuckets")
        shutil.copytree(MOD, mod)
        cfg = os.path.join(mod, "config.txt")
        if config_text is None:
            os.remove(cfg)
        else:
            open(cfg, "w").write(config_text)
        lua = lua54.LuaRuntime(unpack_returned_tuples=True)
        env = lua.execute(MOCK)
        main = os.path.join(mod, "Scripts", "main.lua").replace("\\", "/")
        lua.execute(f'dofile("{main}")')
        print(f"--- {title}")
        steps(lua, env)
        for line in env.logs.values():
            print("   ", line)
        return env
    finally:
        shutil.rmtree(tmp)


def add(lua, env, name, cap=None):
    c, p = VANILLA.get(name, (cap, 5))
    env.objects[name] = env.make(name, cap or c, p)
    env.loaded[name] = True


def cap(env, name):
    return env.objects[name].Capacity


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)
            print("    FAIL:", msg)

    # Lua 5.4 syntax for every script.
    for root, _dirs, files in os.walk(MOD):
        for f in files:
            if f.endswith(".lua"):
                path = os.path.join(root, f)
                lua = lua54.LuaRuntime()
                ok = lua.eval(f'(function() local f, e = loadfile("{path.replace(chr(92), "/")}") return f ~= nil or e end)()')
                print(f"syntax {os.path.relpath(path, REPO)}: {'ok' if ok is True else ok}")
                check(ok is True, f"syntax error in {f}: {ok}")

    def shipped(lua, env):
        for n in ("ITEM_Bucket_Compost", "ITEM_WateringCan_Wood", "ITEM_WateringCan_Bronze", "ITEM_WateringCan_Steel"):
            add(lua, env, n)
        add(lua, env, "ITEM_SomeFutureCan", 500)
        env.tick()
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 450, "bucket 150 -> 450")
        check(cap(env, "ITEM_WateringCan_Steel") == 900, "steel 300 -> 900")
        check(cap(env, "ITEM_SomeFutureCan") == 500, "unknown container untouched")
        add(lua, env, "ITEM_WateringCan_Rune")
        env.tick()
        check(cap(env, "ITEM_WateringCan_Rune") == 1200, "late-loading rune can 400 -> 1200")
        env.objects["ITEM_Bucket_Compost"] = env.make("ITEM_Bucket_Compost", 150, 10)
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 450, "reloaded bucket re-applied once, not compounded")
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 450, "stays 450 on later ticks")
    run_case("shipped config.txt", open(os.path.join(MOD, "config.txt")).read(), shipped)

    def custom(lua, env):
        add(lua, env, "ITEM_Bucket_Compost")
        add(lua, env, "ITEM_WateringCan_Wood")
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 375, "bucket x2.5 -> 375")
        check(cap(env, "ITEM_WateringCan_Wood") == 200, "cans x1 stay vanilla")
    run_case("custom values, inline comments", "compost_bucket = 2.5 ; comment\nwatering_cans=1\n", custom)

    def bad(lua, env):
        add(lua, env, "ITEM_Bucket_Compost")
        add(lua, env, "ITEM_WateringCan_Wood")
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 150, "bucket 0.5 clamped to 1")
        check(cap(env, "ITEM_WateringCan_Wood") == 600, "non-number falls back to default 3")
    run_case("bad values", "compost_bucket = 0.5\nwatering_cans = lots\nbogus = 2\n", bad)

    def missing(lua, env):
        add(lua, env, "ITEM_Bucket_Compost")
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 450, "defaults when config.txt is missing")
    run_case("no config.txt", None, missing)

    def other_mod(lua, env):
        add(lua, env, "ITEM_Bucket_Compost", 300)
        env.tick()
        check(cap(env, "ITEM_Bucket_Compost") == 900, "pak-changed base 300 -> 900")
    run_case("another mod already set 300", "compost_bucket = 3\n", other_mod)

    print()
    if failures:
        print(f"{len(failures)} FAILED")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
