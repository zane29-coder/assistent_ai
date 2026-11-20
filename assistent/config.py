"""Sozlamalarni saqlash va o'qish (config.json)."""

import json
import os
import sys
from pathlib import Path


def _data_dir() -> Path:
    """Sozlamalar saqlanadigan papka.

    .exe ko'rinishida: %APPDATA%\\AssistentAI (yozish ruxsati doim bor).
    Manba koddan ishga tushirilganda: loyiha papkasi.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or str(Path.home())
        d = Path(base) / "AssistentAI"
    else:
        d = Path(__file__).resolve().parent.parent
    d.mkdir(parents=True, exist_ok=True)
    return d


APP_DIR = _data_dir()
CONFIG_PATH = APP_DIR / "config.json"
TASKS_PATH = APP_DIR / "tasks.json"

DEFAULTS = {
    "api_key": "",
    "model": "claude-opus-5-5",
    # low / medium / high / xhigh / max. Ekran bilan ishlash uchun "medium" yaxshi muvozanat.
    "effort": "medium",
    # Bitta vazifada eng ko'p nechta qadam (API so'rovi) qilinsin.
    "max_steps": 60,
    # Skrinshot uzun tomoni (piksel). Kichikroq = arzonroq, lekin mayda yozuvlar xiraroq.
    "screenshot_long_edge": 1366,
    # Vazifa ishlayotganda asosiy oynani yashirish (ekranni to'smasligi uchun).
    "hide_window_while_running": True,
    # Har bir amal orasidagi kutish (soniya).
    "action_delay": 0.4,
    # Tezkor tugmalar (butun Windows bo'ylab ishlaydi).
    "hotkey_start": "ctrl+alt+s",
    "hotkey_pause": "ctrl+alt+p",
    "hotkey_screenshot": "ctrl+alt+r",
    "hotkey_stop": "ctrl+alt+x",
    "hotkey_region": "ctrl+alt+l",
    "hotkey_border": "ctrl+alt+h",
    # Qizil chegara chizig'i ekranda ko'rinsinmi (cheklovning o'ziga ta'sir qilmaydi).
    "show_region_border": False,
    # Maxfiylik chegarasi: [x, y, kenglik, balandlik] asosiy monitorga nisbatan, yoki null.
    "privacy_region": None,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
    if not cfg.get("api_key"):
        cfg["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
