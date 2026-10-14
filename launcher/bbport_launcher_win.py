#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Small offline launcher for Gravity Rush Remastered and Gravity Rush 2."""
import ctypes
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

FROZEN = getattr(sys, 'frozen', False)
PORT_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get('BB_DATA_DIR', PORT_DIR))
CONFIG_FILE = DATA_DIR / 'gravity-launcher.json'
sys.path.insert(0, str(PORT_DIR / 'scripts'))
from game_profiles import effective_fps, inspect_game


def attach_stdio():
    if os.name != 'nt':
        return
    import msvcrt
    for name, std in (('stdout', -11), ('stderr', -12)):
        if getattr(sys, name) is not None:
            continue
        stream = None
        handle = ctypes.windll.kernel32.GetStdHandle(std)
        if handle and handle != ctypes.c_void_p(-1).value:
            try:
                stream = open(msvcrt.open_osfhandle(handle, os.O_WRONLY), 'w', encoding='utf-8',
                              errors='replace', buffering=1)
            except OSError:
                pass
        setattr(sys, name, stream or open(os.devnull, 'w'))


def run_role(argv):
    """Packaged launcher also hosts preparation scripts and the Windows runner."""
    attach_stdio()
    if argv[0] == '--script':
        path, sys.argv = argv[1], argv[1:]
    else:
        path = str(PORT_DIR / 'run.py')
        sys.argv = [path, *argv[1:]]
    try:
        runpy.run_path(path, run_name='__main__')
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else int(stop.code is not None)
    return 0


def load_settings():
    try:
        settings = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        return settings if isinstance(settings, dict) else {}
    except (OSError, ValueError):
        return {}


def launch_environment(game, fps):
    profile, values = inspect_game(game)
    env = dict(os.environ, BB_GAME_DIR=str(Path(game).resolve()), BB_DATA_DIR=str(DATA_DIR.resolve()))
    # A single launcher can switch titles without sharing saves or GPU caches.
    env['BB_USER_DIR'] = str((DATA_DIR / 'user' / values['TITLE_ID']).resolve())
    env['BB_GPU_USER_DIR'] = env['BB_USER_DIR']
    env['BB_FPS'] = effective_fps(profile, values, fps)
    return env, profile


def run_command():
    if os.name == 'nt':
        return [sys.executable, '--run'] if FROZEN else [sys.executable, str(PORT_DIR / 'run.py')]
    return ['bash', str(PORT_DIR / 'run.sh')]


def start_game(game, fps, args=()):
    env, profile = launch_environment(game, fps)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_path = DATA_DIR / 'last_run.log'
    with log_path.open('w', encoding='utf-8') as log:
        log.write(f'{profile.name}\n')
        log.flush()
        process = subprocess.Popen([*run_command(), *args], cwd=PORT_DIR, env=env,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return process


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ('--run', '--script'):
        return run_role(argv)
    settings = load_settings()
    if argv and argv[0] == '--play' and settings.get('game_dir'):
        try:
            return start_game(settings['game_dir'], settings.get('fps', '60'), argv[1:]).wait()
        except (OSError, ValueError) as error:
            attach_stdio()
            print(error, file=sys.stderr)
            return 1

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    root = tk.Tk()
    root.title('Gravity Rush')
    root.geometry('640x330')
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Gravity Rush Remastered / Gravity Rush 2', font=('', 16, 'bold')).pack(anchor='w')
    ttk.Label(frame, text='Experimental PS4 native runtime · offline').pack(anchor='w', pady=(4, 18))
    game = tk.StringVar(value=settings.get('game_dir', ''))
    row = ttk.Frame(frame)
    row.pack(fill='x')
    ttk.Entry(row, textvariable=game).pack(side='left', fill='x', expand=True)
    def browse():
        folder = filedialog.askdirectory(title='Choose the folder containing eboot.bin')
        if folder:
            game.set(folder)
    ttk.Button(row, text='Game folder…', command=browse).pack(side='right', padx=(8, 0))
    fps = tk.StringVar(value=settings.get('fps', '60'))
    ttk.Label(frame, text='Gravity Rush 2 v01.11 FPS patch (Remastered keeps its own timing)').pack(anchor='w', pady=(16, 4))
    ttk.Combobox(frame, values=('30', '60', '90', 'uncap'), textvariable=fps, state='readonly', width=12).pack(anchor='w')
    status = tk.StringVar(value='Graphics and controller settings: Insert / L3+R3 in-game.')
    ttk.Label(frame, textvariable=status, wraplength=590).pack(anchor='w', pady=14)
    process = None
    def poll():
        nonlocal process
        if process is None:
            return
        result = process.poll()
        if result is None:
            root.after(500, poll)
            return
        status.set(f'Game exited ({result}). Log: {DATA_DIR / "last_run.log"}')
        process = None
        play.configure(state='normal')
    def play_game():
        nonlocal process
        try:
            inspect_game(game.get())
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps({'game_dir': game.get(), 'fps': fps.get()}, indent=2), encoding='utf-8')
            process = start_game(game.get(), fps.get())
        except (OSError, ValueError) as error:
            messagebox.showerror('Gravity Rush', str(error))
            return
        play.configure(state='disabled')
        status.set(f'Running. Log: {DATA_DIR / "last_run.log"}')
        root.after(500, poll)
    play = ttk.Button(frame, text='PLAY', command=play_game)
    play.pack(anchor='e')
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
