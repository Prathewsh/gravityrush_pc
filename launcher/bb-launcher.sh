#!/usr/bin/env bash
# Starts the Gravity Rush launcher (Tk). With Python and Tk installed
# it runs directly; otherwise through nix-shell (launcher/shell.nix).
here=$(cd -- "$(dirname -- "$0")" && pwd)
if python3 -c 'import tkinter' 2>/dev/null; then
    exec python3 "$here/bbport_launcher.py" "$@"
fi
exec nix-shell "$here/shell.nix" --run "python3 '$here/bbport_launcher.py'"
