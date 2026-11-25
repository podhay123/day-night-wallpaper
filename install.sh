#!/usr/bin/env bash
# Installs the day/night wallpaper for the current user (KDE Plasma 5).
# Safe to run again after pulling changes.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
UNITS="$HOME/.config/systemd/user"

missing=0
for c in python3 qdbus gdbus plasma-apply-wallpaperimage plasma-apply-colorscheme \
         kreadconfig5 kwriteconfig5 systemctl curl; do
  command -v "$c" >/dev/null || { echo "Missing command: $c" >&2; missing=1; }
done
python3 -c 'import PIL' 2>/dev/null || { echo "Missing Python Pillow (Debian/Ubuntu: sudo apt install python3-pil)" >&2; missing=1; }
(( missing )) && exit 1

[[ -f "$REPO/day.jpg" && -f "$REPO/night.jpg" ]] || "$REPO/fetch-paintings.sh"

# Commands: day-night-wallpaper, day, night, wallpaper
mkdir -p "$BIN" "$APPS" "$UNITS"
chmod +x "$REPO/day-night-wallpaper"
ln -sfn "$REPO/day-night-wallpaper" "$BIN/day-night-wallpaper"
for n in day night wallpaper; do ln -sfn day-night-wallpaper "$BIN/$n"; done
case ":$PATH:" in *":$BIN:"*) ;; *) echo "Note: add $BIN to your PATH to use the day/night/wallpaper commands." ;; esac

# KRunner / menu entries
entry() { # file name exec icon keywords
  cat > "$APPS/$1" <<DESKTOP
[Desktop Entry]
Type=Application
Name=$2
Comment=Day/night wallpaper (Tsarouchis, Neon Cafe)
Exec=$3
Icon=$4
Keywords=$5
Categories=Settings;DesktopSettings;
Terminal=false
StartupNotify=false
DESKTOP
}
entry wallpaper-day.desktop    "Wallpaper: Day"              "$BIN/day"              weather-clear                 "wallpaper;day;light;sun;"
entry wallpaper-night.desktop  "Wallpaper: Night"            "$BIN/night"            weather-clear-night           "wallpaper;night;dark;moon;"
entry wallpaper-auto.desktop   "Wallpaper: Automatic"        "$BIN/wallpaper auto"   weather-few-clouds            "wallpaper;auto;automatic;sunrise;sunset;"
entry wallpaper-toggle.desktop "Wallpaper: Toggle Day/Night" "$BIN/wallpaper toggle" preferences-desktop-wallpaper "wallpaper;toggle;switch;day;night;"
command -v kbuildsycoca5 >/dev/null && kbuildsycoca5 >/dev/null 2>&1 || true

# Global shortcuts Meta+Shift+D / N / A (skipped if the key is taken by something else)
KGA=(gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel --method)
shortcut() { # desktop-file friendly-name key-name qt-key
  local code=$(( 0x10000000 | 0x02000000 | $4 )) id="['$1', '_launch', '$2', '$2']" owners
  owners=$("${KGA[@]}" org.kde.KGlobalAccel.getGlobalShortcutsByKey "$code" 2>/dev/null) || {
    echo "Could not reach the shortcut service; set Meta+Shift+$3 for \"$2\" in System Settings → Shortcuts."; return; }
  if [[ "$owners" == *"('"* && "$owners" != *"'$1'"* ]]; then
    echo "Meta+Shift+$3 is already used by something else; not assigning it to \"$2\"."; return
  fi
  "${KGA[@]}" org.kde.KGlobalAccel.doRegister "$id" >/dev/null
  "${KGA[@]}" org.kde.KGlobalAccel.setForeignShortcut "$id" "[$code]" >/dev/null
}
shortcut wallpaper-day.desktop   "Wallpaper: Day"       D 0x44
shortcut wallpaper-night.desktop "Wallpaper: Night"     N 0x4E
shortcut wallpaper-auto.desktop  "Wallpaper: Automatic" A 0x41

# Timer: every 5 minutes and at login
cp "$REPO/systemd/day-night-wallpaper.service" "$REPO/systemd/day-night-wallpaper.timer" "$UNITS/"
systemctl --user daemon-reload
systemctl --user enable day-night-wallpaper.service >/dev/null 2>&1
systemctl --user enable --now day-night-wallpaper.timer >/dev/null 2>&1
systemctl --user start --no-block day-night-wallpaper.service

echo "Installed. Try: wallpaper status"
