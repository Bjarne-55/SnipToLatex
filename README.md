# SnipToLatex

Capture a screen region and convert it to LaTeX. The LaTeX is copied to your clipboard automatically.

## Install
- Requirements: Python 3.9+ and a desktop environment (Windows or Linux/X11 recommended).
- From source (at the moment only option):
  1) Clone this repo and open it in a terminal.
  2) Create a virtual env and install:
     - `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\\Scripts\\activate`)
     - `pip install -U pip wheel`
     - `pip install .`
  3) Run with `snip-to-latex` or `python snip_to_latex.py`.

## Use
- Start the tray app: run `snip-to-latex` (after install) or `python snip_to_latex.py` in this repo.
- Press `Win/Super + Shift + C`, then drag to select a region of your screen.
- The image is sent to the selected model (Gemini by default); the generated LaTeX is copied to your clipboard and a small toast confirms success.

## Add Your API Key
- Open the app’s tray icon menu and choose `Settings`.
- In "Model", select `Gemini` (default). Paste your Google AI Studio API key into "API Key" and click `Save`.
- The prompt used for conversion can also be customized in this dialog.

Config is stored per‑user:
- Windows: `%APPDATA%/SnipToLatex/config.ini`
- Linux/macOS: `$XDG_CONFIG_HOME/SnipToLatex/config.ini` or `~/.config/SnipToLatex/config.ini`

Notes:
- Screen capture and global hotkeys may be restricted under Wayland; X11/Windows work best.
- Only Gemini is implemented today; other model choices are placeholders.
