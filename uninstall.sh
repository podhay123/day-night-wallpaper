#!/usr/bin/env bash
# Removes the day/night wallpaper. Your current wallpaper and colour scheme stay as they are.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"

systemctl --user disable --now day-night-wallpaper.timer day-night-wallpaper.service >/dev/null 2>&1
rm -f "$HOME/.config/systemd/user/day-night-wallpaper.service" "$HOME/.config/systemd/user/day-night-wallpaper.timer"
systemctl --user daemon-reload

for f in wallpaper-day wallpaper-night wallpaper-auto; do
  gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
    --method org.kde.KGlobalAccel.unregister "$f.desktop" "_launch" >/dev/null 2>&1
done
rm -f "$HOME"/.local/share/applications/wallpaper-{day,night,auto,toggle}.desktop
command -v kbuildsycoca5 >/dev/null && kbuildsycoca5 >/dev/null 2>&1

# remove only links that point at this repo's script
for n in day-night-wallpaper day night wallpaper; do
  [[ -L "$BIN/$n" && "$(readlink -f "$BIN/$n")" == "$REPO/day-night-wallpaper" ]] && rm -f "$BIN/$n"
done
rm -rf "$HOME/.local/share/day-night-wallpaper"
echo "Uninstalled."
