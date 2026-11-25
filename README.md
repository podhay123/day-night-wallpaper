# Day/night wallpaper: Tsarouchis, "Neon Cafe"

A KDE Plasma wallpaper that follows the sun. From sunrise to sunset the desktop shows
Yannis Tsarouchis' *"Neon" Cafe (Daytime)*; after sunset it shows *"Neon" Cafe (Night)*.

Both paintings show the same café façade in Omonia Square, Athens. The wallpaper is a close-up
crop of each in which the NEON sign sits in exactly the same spot and at the same size, so at dusk
the building stays still and only the light changes: the windows light up and the customers
appear (a smooth fade of about 20 s). Along with the wallpaper, these switch too:

- colour scheme: light Breeze with a blue accent (the kiosk) by day, dark Breeze with an amber accent (the café windows) at night,
- the lock screen picture.

Sunrise and sunset are computed offline from a latitude/longitude in the script (default: Warsaw).

## Requirements

- KDE Plasma 5 (tested on Plasma 5.27, Wayland, Debian 12)
- Python 3 with Pillow (`sudo apt install python3-pil`)
- `qdbus`, `gdbus`, `curl`, `kreadconfig5` / `kwriteconfig5`, `plasma-apply-wallpaperimage`, `plasma-apply-colorscheme` (all present on a standard Plasma install)
- systemd user session

## Install

```bash
git clone https://github.com/podhay123/day-night-wallpaper.git
cd day-night-wallpaper
./install.sh
```

`install.sh` downloads the paintings (see below), links the commands into `~/.local/bin`, adds KRunner
entries and keyboard shortcuts, and enables a systemd user timer. Keep the cloned folder where it is:
the installed commands point into it, and the paintings live there. Run `./install.sh` again after `git pull`.

### About the paintings

Yannis Tsarouchis (1910–1989) is still under copyright, so the images are **not** in this repository.
`./fetch-paintings.sh` (called by the installer) downloads them from the
[National Gallery – Alexandros Soutsos Museum](https://www.nationalgallery.gr/en/artwork/neon-cafe-night/) website
into the repo folder ([daytime](https://www.nationalgallery.gr/en/artwork/neon-cafe-daytime-9547/),
[night](https://www.nationalgallery.gr/en/artwork/neon-cafe-night/)). They are ignored by git.

## Usage

### Terminal commands

| Command | What it does |
|---|---|
| `day` | ☀ forces day until the next sunrise/sunset, then back to automatic |
| `night` | ☾ forces night until the next sunrise/sunset, then back to automatic |
| `wallpaper auto` | back to automatic mode |
| `wallpaper toggle` | switches to the opposite mode |
| `wallpaper status` | shows what is set now and when the next change happens |
| `wallpaper` | current state plus the list of commands |
| `wallpaper help` | short help |

Example: at 2 pm you type `night`. Night stays until sunset, and from then on it is night anyway.
If you type `day` at 9 pm, day stays until morning, and from sunrise everything works as usual again.

### Keyboard shortcuts

| Shortcut | What it does |
|---|---|
| **Meta+Shift+D** | day |
| **Meta+Shift+N** | night |
| **Meta+Shift+A** | automatic |

(Meta is the key with the Windows logo.) After a shortcut, a notification tells you how long the change will last.
The installer skips a shortcut if the key is already taken. You can change them in
System Settings → Shortcuts → "Wallpaper: …".

### KRunner / application menu

Press **Alt+Space** and type `wallpaper`, `day` or `night`. You will find
"Wallpaper: Day", "Wallpaper: Night", "Wallpaper: Automatic" and "Wallpaper: Toggle Day/Night".

## Customising

All settings are at the top of [`day-night-wallpaper`](day-night-wallpaper):

| Setting | What it changes |
|---|---|
| `LATITUDE`, `LONGITUDE` | your location, which sets the sunrise and sunset times |
| `SCREEN_W`, `SCREEN_H`, `PANEL_LEFT` | screen size and the width of a panel on the left (the sign is centred next to it) |
| `NEON_Y`, `NEON_X` | where the NEON sign sits on the screen |
| `NEON_SIZE` | size of the sign: a bigger value means a closer crop (but a softer image) |
| `SWITCH_THEME = False` | stops switching the light/dark colour scheme (so you can set it yourself) |
| `SWITCH_LOCKSCREEN = False` | stops changing the lock screen |
| `TRANSITION_FRAMES`, `TRANSITION_STEP_S` | length of the fade at dusk and dawn |

After changing a setting or replacing `day.jpg` / `night.jpg`, the wallpapers are re-rendered automatically on the
next run (within 5 minutes, or right away with `wallpaper auto`). If you use other images, measure the box around
the NEON lettering and put it in `STYLE[...]["neon"]`.

## How it works

- A systemd user timer runs `day-night-wallpaper` every 5 minutes and at login. It works out whether it is day or
  night (or whether you forced a mode), and only changes something when needed.
- The two close-ups are rendered once with Pillow (Lanczos, light sharpening) into
  `~/.local/share/day-night-wallpaper/`, together with 15 blended frames for the fade.
  Plasma's own wallpaper fade can't be lengthened in 5.27, so the script steps through the frames itself.
- `day` / `night` write a small override file that expires at the next sunrise or sunset, then start the
  service in the background so the terminal or shortcut doesn't wait for the fade.

## Files

| Path | What it is |
|---|---|
| this folder | the script, the paintings (`day.jpg`, `night.jpg`) and the installer |
| `~/.local/bin/day-night-wallpaper` (+ `day`, `night`, `wallpaper`) | links to the script |
| `~/.local/share/day-night-wallpaper/` | rendered wallpapers, fade frames and the override file |
| `~/.config/systemd/user/day-night-wallpaper.{service,timer}` | the timer |
| `~/.local/share/applications/wallpaper-*.desktop` | KRunner entries, also used by the shortcuts |

## Troubleshooting

```bash
wallpaper status                                       # what should be set vs. what is set
journalctl --user -u day-night-wallpaper -n 20         # recent messages
systemctl --user list-timers day-night-wallpaper.timer # when the next check runs
```

## Uninstall

```bash
./uninstall.sh
```

This removes the timer, commands, shortcuts and rendered files. Your current wallpaper and colour scheme stay as they are.
