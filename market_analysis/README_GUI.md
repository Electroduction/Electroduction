# 🖥️ GUI Installation Note

## tkinter Requirement

The trading GUI uses **tkinter** which is Python's standard GUI library. It comes pre-installed with Python on most systems.

### If you see "No module named 'tkinter'"

**On Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**On Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**On macOS:**
- tkinter comes with Python (no action needed)
- If missing: `brew install python-tk`

**On Windows:**
- tkinter comes with Python (no action needed)
- If missing: Reinstall Python from python.org with GUI support

### Verify tkinter is available

```bash
python -c "import tkinter; print('✓ tkinter is available')"
```

If you see "✓ tkinter is available", you're ready to run the GUI!

```bash
python trading_gui.py
```

---

## Alternative: Command Line Demo

If you can't use the GUI (headless server, etc.), you can still use the analysis system:

```bash
# Run pattern detection demo
python core/pattern_detector.py

# Run comprehensive analysis demo
python demo_comprehensive.py

# Run pattern database demo
python data/pattern_database.py
```

These provide full analysis without GUI!
