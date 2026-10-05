-- Bigger Buckets: the Compost Bucket and watering cans hold more.
--
-- Each container is a HeldContainerEquipmentData asset (/Script/Dominion).
-- Its int32 Capacity is how much one fill holds; AmountDischargedPerUse and
-- PlotDischargeMultiplier, which set how fast it empties, are left alone.
-- Items in a bag store only their content and Quantity, so every bucket and
-- can, old or new, reads the raised Capacity from the asset.

local VERSION = "1.0.0"

local function log(msg)
    print("[Bigger Buckets] " .. msg .. "\n")
end

local function script_dir()
    local source = debug.getinfo(1, "S").source
    source = source:match("^@(.*)$") or source
    return source:match("^(.*)[/\\]")
end

local HELD = "/Game/Gameplay/Character/Player/Equipment/Held/Bucket/"

local ITEMS = {
    { path = HELD .. "ITEM_Bucket_Compost.ITEM_Bucket_Compost", group = "compost_bucket" },
    { path = HELD .. "ITEM_WateringCan_Wood.ITEM_WateringCan_Wood", group = "watering_cans" },
    { path = HELD .. "ITEM_WateringCan_Bronze.ITEM_WateringCan_Bronze", group = "watering_cans" },
    { path = HELD .. "ITEM_WateringCan_Steel.ITEM_WateringCan_Steel", group = "watering_cans" },
    { path = "/UmbralSands/Gameplay/Character/Player/Equipment/Held/Bucket/ITEM_WateringCan_Adamant.ITEM_WateringCan_Adamant", group = "watering_cans" },
    { path = "/ScornedWilderness/Gameplay/Character/Player/Equipment/Held/Bucket/ITEM_WateringCan_Rune.ITEM_WateringCan_Rune", group = "watering_cans" },
}

local DEFAULTS = { compost_bucket = 3, watering_cans = 3 }
local MIN, MAX = 1, 20

local function read_config(path)
    local cfg = {}
    for k, v in pairs(DEFAULTS) do cfg[k] = v end
    local f = path and io.open(path, "r")
    if not f then
        log("config.txt not found, using defaults")
        return cfg
    end
    for line in f:lines() do
        local key, value = line:gsub("[;#].*$", ""):match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
        if key then
            if DEFAULTS[key] == nil then
                log("config.txt: unknown setting '" .. key .. "' ignored")
            else
                local n = tonumber(value)
                if not n then
                    log("config.txt: " .. key .. " = '" .. value .. "' is not a number, using " .. DEFAULTS[key])
                elseif n < MIN or n > MAX then
                    local clamped = math.max(MIN, math.min(MAX, n))
                    log("config.txt: " .. key .. " = " .. value .. " is outside " .. MIN .. "-" .. MAX .. ", using " .. clamped)
                    cfg[key] = clamped
                else
                    cfg[key] = n
                end
            end
        end
    end
    f:close()
    return cfg
end

local dir = script_dir()
local config = read_config(dir and (dir .. "\\..\\config.txt"))

log(string.format("Loaded %s. Compost Bucket x%s, watering cans x%s", VERSION,
    tostring(config.compost_bucket), tostring(config.watering_cans)))

local function valid(obj)
    local ok, yes = pcall(function() return obj ~= nil and obj:IsValid() end)
    return ok and yes
end

local function short(path)
    return path:match("%.([^%.]+)$") or path
end

-- Capacity each asset had before this mod touched it, so re-applying after a
-- reload or a world change never multiplies twice. Another mod's pak that
-- changes Capacity becomes the base this multiplies.
local original = {}
local applied = {}
local reported = {}

local function apply(item)
    local obj = StaticFindObject(item.path)
    if not valid(obj) then return false end
    local ok, cur = pcall(function() return obj.Capacity end)
    if not ok or type(cur) ~= "number" then
        if not reported[item.path] then
            reported[item.path] = true
            log(short(item.path) .. ": no Capacity property, left unchanged")
        end
        return false
    end
    local base = original[item.path]
    if base == nil then
        base = cur
        original[item.path] = cur
    end
    local target = math.floor(base * config[item.group] + 0.5)
    if cur == target then return true end
    if cur ~= base and applied[item.path] ~= cur then
        -- Something else changed it since we last looked; treat that as the new base.
        base = cur
        original[item.path] = cur
        target = math.floor(base * config[item.group] + 0.5)
    end
    local wrote = pcall(function() obj.Capacity = target end)
    local now = nil
    pcall(function() now = obj.Capacity end)
    if wrote and now == target then
        applied[item.path] = target
        local perUse, mult = "?", "?"
        pcall(function() perUse = tostring(obj.AmountDischargedPerUse) end)
        pcall(function() mult = tostring(obj.PlotDischargeMultiplier) end)
        log(string.format("%s: Capacity %d -> %d (per use %s, plot multiplier %s)",
            short(item.path), base, target, perUse, mult))
    elseif not reported[item.path .. "|write"] then
        reported[item.path .. "|write"] = true
        log(short(item.path) .. ": could not set Capacity (still " .. tostring(now) .. ")")
    end
    return true
end

local listedOthers = false
local known = {}
for _, item in ipairs(ITEMS) do known[short(item.path)] = true end

-- Once, after the base-game containers exist, name any other container asset
-- so a game update that adds one shows up in the log instead of silently
-- staying small.
local function list_others()
    local all = FindAllOf("HeldContainerEquipmentData") or {}
    for _, obj in ipairs(all) do
        local name = nil
        pcall(function() name = obj:GetFName():ToString() end)
        if name and not known[name] and not name:find("^Default__") then
            local cap = "?"
            pcall(function() cap = tostring(obj.Capacity) end)
            log("Other container left unchanged: " .. name .. " (Capacity " .. cap .. ")")
        end
    end
    listedOthers = true
end

local function tick()
    local baseFound = 0
    for i, item in ipairs(ITEMS) do
        if apply(item) and i <= 4 then baseFound = baseFound + 1 end
    end
    if not listedOthers and baseFound == 4 then list_others() end
end

local run = ExecuteInGameThread or function(fn) fn() end

if LoopAsync then
    local lastError = nil
    LoopAsync(3000, function()
        run(function()
            local ok, err = pcall(tick)
            if not ok and tostring(err) ~= lastError then
                lastError = tostring(err)
                log("Update failed: " .. lastError)
            end
        end)
        return false
    end)
else
    log("LoopAsync is missing; this UE4SS build cannot run Bigger Buckets")
end
