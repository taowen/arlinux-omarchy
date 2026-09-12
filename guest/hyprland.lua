local files = assert(os.getenv('XDG_RUNTIME_DIR')):gsub('/runtime$', '')
local omarchy = files .. '/rootfs/usr/share/omarchy'
hl.env('HOME', files .. '/home')
hl.env('XDG_CONFIG_HOME', files .. '/home/.config')
hl.env('OMARCHY_PATH', omarchy)
hl.env('ARLINUX_EXEC_WRAPPER', files .. '/rootfs/usr/lib/arlinux/guest/host-exec.sh')

dofile(omarchy .. '/default/hypr/bootstrap.lua')
-- Android owns service lifetime; the product's D-Bus session starts the shell.
package.loaded['default.hypr.autostart'] = true
package.loaded['default.hypr.nvidia'] = true
omarchy_preinstalled_bindings = false
require('default.hypr.omarchy')
o.launch = function(command) return command end
hl.monitor({ output = '', mode = 'preferred', position = 'auto', scale = 1.5 })
hl.config({ misc = { disable_hyprland_guiutils_check = true, disable_watchdog_warning = true }, debug = { disable_logs = false } })
hl.bind('ALT + F4', hl.dsp.window.close())
-- This Xwayland exposes a 32-bit default visual. XTerm's core X11 erases
-- write RGB background pixels with an unused zero high byte. Ignore that
-- byte for XTerm so cleared cells stay filled; retain theme window opacity.
hl.window_rule({ match = { class = '^(XTerm|UXTerm)$' }, force_rgbx = true })

local optional = require('default.hypr.require_optional')
for _, module in ipairs({ 'input', 'bindings', 'looknfeel', 'autostart' }) do
  optional.module('hypr.' .. module)
end
