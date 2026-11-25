#!/usr/bin/env bash
# Downloads the two paintings from the National Gallery of Athens website.
# Yannis Tsarouchis (1910-1989), "Neon" Cafe (Daytime) and "Neon" Cafe (Night).
# The works are still under copyright, so they are not part of this repository.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

fetch() { # name url sha256
  local out="$DIR/$1.jpg"
  if [[ -f "$out" ]]; then
    echo "$1.jpg already there"
  else
    echo "Downloading $1.jpg ..."
    curl -fsSL --retry 3 -o "$out.part" "$2"
    mv "$out.part" "$out"
  fi
  if ! echo "$3  $out" | sha256sum --check --status; then
    echo "Note: $1.jpg differs from the file the NEON position was measured on." >&2
    echo "      If the sign ends up in the wrong place, adjust STYLE[\"$1\"][\"neon\"] in day-night-wallpaper." >&2
  fi
}

fetch day   https://www.nationalgallery.gr/wp-content/uploads/2025/09/60798_2000_2000.jpg \
            5f477a76078b5066ac6c3537bc73182671e5e6f34e3e5aeb2b75944f1fe82d4d
fetch night https://www.nationalgallery.gr/wp-content/uploads/2023/07/60835_2000_2000.jpg \
            4c54de530637f0c0b17cb79574570d29680eb1e4086cab80e9c13b2c80e6b991
