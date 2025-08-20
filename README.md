# SnipToLatex

Minimal headless snipping tool written in Python.

- Global hotkey (Windows): Ctrl + Win + C
- Global hotkey (Linux/X11 fallback): Ctrl + Shift + C (if Win key cannot be bound)
- Action: Draw a rectangle to capture; the image is copied to the clipboard.
- Platforms: Windows, Linux (X11). Note: Wayland restricts screen capture and global hotkeys; see notes below.

## Setup

### Example config.ini
```
[sniptolatex]
# Put your Gemini/Google API key here (uncomment and set):
# api_key = MY_KEY
```

