"""Configuration manager for Disk Analyzer."""
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/disk-analyzer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "language": "en",           # Default language is English ("en" or "ru")
    "benchmark_size_mb": "1024",# Default benchmark test file size (1 GB)
    "advanced_mode": False,     # Expert SMART view toggle
    "hide_bench_tip": False,    # Tip notification
}

def get_settings() -> dict:
    """Load settings from JSON file, falling back to defaults."""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
        except Exception:
            pass

    settings = dict(DEFAULT_SETTINGS)
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    settings.update(saved)
        except Exception as e:
            print(f"[Settings] Error loading config: {e}")

    return settings

def save_settings(settings: dict) -> bool:
    """Save settings dictionary to JSON file."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Settings] Error saving config: {e}")
        return False

def get_setting(key: str, default=None):
    settings = get_settings()
    return settings.get(key, DEFAULT_SETTINGS.get(key, default))

def set_setting(key: str, value) -> bool:
    settings = get_settings()
    settings[key] = value
    return save_settings(settings)
