-- luacheck configuration for addon code checked by Better Addons.
-- Rule: everything in your own namespace, no unprefixed globals.

std = "lua51"
max_line_length = 120

-- Globals the game itself provides are read-only, not ours to define.
read_globals = {
    "C_Timer", "C_Map", "C_QuestLog", "C_AddOns", "C_CVar",
    "CreateFrame", "UIParent", "WorldMapFrame", "Minimap",
    "GetTime", "GetBuildInfo", "GetAddOnMetadata", "IsAddOnLoaded",
    "SlashCmdList", "SLASH_BETTERADDONS1",
    "hooksecurefunc", "issecurevariable", "InCombatLockdown",
    "SetCVar", "GetCVar", "MuteSoundFile", "SpeakText",
    "print", "unpack", "wipe", "strsplit", "strjoin", "format",
}

-- The one global an addon is expected to write: its own module report.
globals = { "BetterAddons_Active" }

ignore = {
    "212/self",  -- unused self in methods is idiomatic
}

exclude_files = { "_site/**", ".venv/**" }
