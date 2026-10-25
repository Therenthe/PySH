-- App-owned inspection only. No filenames/URLs from metadata are opened.
local mp = require 'mp'
local utils = require 'mp.utils'
local sent = false
local function text(value)
    if type(value) == 'string' and #value <= 1024 then return value end
    return nil
end
local function tag(name)
    return text(mp.get_property_native('metadata/by-key/' .. name))
        or text(mp.get_property_native('metadata/by-key/' .. string.upper(name)))
end
mp.register_event('file-loaded', function()
    if sent then return end
    sent = true
    local duration = mp.get_property_native('duration')
    if type(duration) ~= 'number' or duration ~= duration or duration <= 0 or duration > 864000 then duration = nil end
    local tracks = {}
    local count = mp.get_property_native('track-list/count', 0)
    if type(count) ~= 'number' then count = 0 end
    for i = 0, math.min(15, count - 1) do
        local prefix = 'track-list/' .. i .. '/'
        local kind = mp.get_property_native(prefix .. 'type')
        if (kind == 'video' or kind == 'audio') and not mp.get_property_native(prefix .. 'external', false) then
            tracks[#tracks + 1] = {type = kind, albumart = mp.get_property_native(prefix .. 'albumart', false) == true}
        end
    end
    local encoded = utils.format_json({duration_s = duration, title = tag('title'), artist = tag('artist'), album = tag('album'), tracks = tracks})
    if encoded and #encoded <= 8192 then
        io.stdout:write('PYSH_MEDIA_V1 ' .. encoded .. '\n')
        io.stdout:flush()
    end
end)
