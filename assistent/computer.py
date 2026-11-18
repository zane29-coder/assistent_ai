"""Ekranni ko'rish va boshqarish: skrinshot, sichqoncha, klaviatura.

Claude'ning `computer_toolset_20260801` a'zo-asboblarini (screenshot, left_click,
type, key, scroll, zoom, ...) haqiqiy kompyuterda bajaradi.
"""

import base64
import io
import platform
import time

from PIL import Image

if platform.system() == "Windows":
    # Windows ekran masshtabi (125%, 150%) koordinatalarni buzmasligi uchun.
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:  # noqa: BLE001
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass

import mss  # noqa: E402
import pyautogui  # noqa: E402
import pyperclip  # noqa: E402

# Sichqonchani ekranning chap-yuqori burchagiga olib borsangiz, amal darhol to'xtaydi.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Claude xdotool uslubidagi tugma nomlarini yuboradi; pyautogui nomlariga o'giramiz.
KEY_MAP = {
    "return": "enter",
    "enter": "enter",
    "kp_enter": "enter",
    "escape": "esc",
    "esc": "esc",
    "super": "win",
    "super_l": "win",
    "meta": "win",
    "cmd": "win",
    "win": "win",
    "control": "ctrl",
    "control_l": "ctrl",
    "ctrl": "ctrl",
    "alt_l": "alt",
    "shift_l": "shift",
    "page_down": "pagedown",
    "page_up": "pageup",
    "next": "pagedown",
    "prior": "pageup",
    "backspace": "backspace",
    "delete": "delete",
    "del": "delete",
    "tab": "tab",
    "space": "space",
    "home": "home",
    "end": "end",
    "insert": "insert",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "minus": "-",
    "plus": "+",
    "equal": "=",
    "comma": ",",
    "period": ".",
    "slash": "/",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "grave": "`",
    "bracketleft": "[",
    "bracketright": "]",
    "caps_lock": "capslock",
    "print": "printscreen",
}


def _map_key(name: str) -> str:
    k = name.strip()
    low = k.lower()
    if low in KEY_MAP:
        return KEY_MAP[low]
    if low.startswith("f") and low[1:].isdigit():
        return low
    return low if len(k) > 1 else k


def _split_combo(combo: str) -> list[str]:
    # "ctrl+s", "ctrl+shift+Tab", "ctrl++" kabi
    parts = combo.split("+")
    keys, i = [], 0
    while i < len(parts):
        p = parts[i]
        if p == "" and i + 1 < len(parts):
            keys.append("+")
            i += 2
            continue
        if p:
            keys.append(_map_key(p))
        i += 1
    return keys


class ActionError(Exception):
    pass


class Computer:
    def __init__(self, long_edge: int = 1366, action_delay: float = 0.4):
        self.long_edge = max(640, min(int(long_edge), 2576))
        self.action_delay = action_delay
        with mss.mss() as sct:
            mon = sct.monitors[1]  # asosiy monitor
        self.monitor = dict(mon)
        self.screen_w = mon["width"]
        self.screen_h = mon["height"]
        self.scale = min(1.0, self.long_edge / max(self.screen_w, self.screen_h))
        # Vizual tokenlar chegarasi (Opus 4.7+): ceil(w/28)*ceil(h/28) <= 4784
        while True:
            w, h = self.img_size()
            if -(-w // 28) * -(-h // 28) <= 4784:
                break
            self.scale *= 0.95

    # --- koordinatalar ---
    def img_size(self) -> tuple[int, int]:
        return max(1, round(self.screen_w * self.scale)), max(1, round(self.screen_h * self.scale))

    def to_screen(self, xy) -> tuple[int, int]:
        if not xy or len(xy) != 2:
            raise ActionError("coordinate [x, y] ko'rinishida bo'lishi kerak")
        x = int(round(xy[0] / self.scale)) + self.monitor["left"]
        y = int(round(xy[1] / self.scale)) + self.monitor["top"]
        x = min(max(x, self.monitor["left"]), self.monitor["left"] + self.screen_w - 1)
        y = min(max(y, self.monitor["top"]), self.monitor["top"] + self.screen_h - 1)
        return x, y

    # --- skrinshot ---
    def _grab(self) -> Image.Image:
        with mss.mss() as sct:
            raw = sct.grab(self.monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    @staticmethod
    def _encode(img: Image.Image) -> dict:
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(buf.getvalue()).decode("ascii"),
            },
        }

    def screenshot_block(self) -> dict:
        img = self._grab()
        if self.scale < 1.0:
            img = img.resize(self.img_size(), Image.LANCZOS)
        return self._encode(img)

    def zoom_block(self, region) -> dict:
        if not region or len(region) != 4:
            raise ActionError("region [x0, y0, x1, y1] ko'rinishida bo'lishi kerak")
        x0, y0, x1, y1 = [v / self.scale for v in region]
        x0, x1 = sorted((max(0, x0), min(self.screen_w, x1)))
        y0, y1 = sorted((max(0, y0), min(self.screen_h, y1)))
        if x1 - x0 < 2 or y1 - y0 < 2:
            raise ActionError("zoom maydoni juda kichik")
        img = self._grab().crop((int(x0), int(y0), int(x1), int(y1)))
        # Kattalashtirilgan rasm ham limitga sig'ishi kerak.
        w, h = img.size
        s = min(self.long_edge / max(w, h), 4.0)
        while -(-int(w * s) // 28) * -(-int(h * s) // 28) > 4784:
            s *= 0.95
        img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
        return self._encode(img)

    # --- yordamchilar ---
    def _with_modifiers(self, mods: str | None, fn):
        keys = _split_combo(mods) if mods else []
        for k in keys:
            pyautogui.keyDown(k)
        try:
            fn()
        finally:
            for k in reversed(keys):
                pyautogui.keyUp(k)

    def _type_text(self, text: str):
        if text.isascii():
            pyautogui.write(text, interval=0.01)
        else:
            # Kirill/o'zbekcha harflar uchun bufer orqali qo'yamiz.
            old = None
            try:
                old = pyperclip.paste()
            except Exception:  # noqa: BLE001
                pass
            pyperclip.copy(text)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.15)
            if old is not None:
                try:
                    pyperclip.copy(old)
                except Exception:  # noqa: BLE001
                    pass

    # --- asosiy dispatcher ---
    def run(self, name: str, inp: dict) -> list[dict] | str:
        """Bitta amalni bajaradi. Natija: rasm bloklari ro'yxati yoki matn."""
        inp = inp or {}
        if name == "screenshot":
            return [self.screenshot_block()]
        if name == "zoom":
            return [self.zoom_block(inp.get("region"))]
        if name == "cursor_position":
            x, y = pyautogui.position()
            ix = round((x - self.monitor["left"]) * self.scale)
            iy = round((y - self.monitor["top"]) * self.scale)
            return f"X={ix}, Y={iy}"

        if name in ("left_click", "right_click", "middle_click", "double_click", "triple_click"):
            button = {"right_click": "right", "middle_click": "middle"}.get(name, "left")
            clicks = {"double_click": 2, "triple_click": 3}.get(name, 1)

            def do():
                if inp.get("coordinate"):
                    x, y = self.to_screen(inp["coordinate"])
                    pyautogui.click(x, y, clicks=clicks, interval=0.08, button=button)
                else:
                    pyautogui.click(clicks=clicks, interval=0.08, button=button)

            self._with_modifiers(inp.get("text"), do)
        elif name == "left_click_drag":
            sx, sy = self.to_screen(inp.get("start_coordinate"))
            ex, ey = self.to_screen(inp.get("coordinate"))

            def do():
                pyautogui.moveTo(sx, sy)
                pyautogui.mouseDown()
                pyautogui.moveTo(ex, ey, duration=0.4)
                pyautogui.mouseUp()

            self._with_modifiers(inp.get("text"), do)
        elif name == "mouse_move":
            x, y = self.to_screen(inp.get("coordinate"))
            pyautogui.moveTo(x, y, duration=0.1)
        elif name == "left_mouse_down":
            pyautogui.mouseDown()
        elif name == "left_mouse_up":
            pyautogui.mouseUp()
        elif name == "scroll":
            direction = inp.get("scroll_direction", "down")
            amount = int(inp.get("scroll_amount", 3))

            def do():
                if inp.get("coordinate"):
                    x, y = self.to_screen(inp["coordinate"])
                    pyautogui.moveTo(x, y)
                if direction in ("up", "down"):
                    pyautogui.scroll((120 if direction == "up" else -120) * amount)
                else:
                    try:
                        pyautogui.hscroll((-120 if direction == "left" else 120) * amount)
                    except Exception:  # noqa: BLE001
                        with pyautogui.hold("shift"):
                            pyautogui.scroll((120 if direction == "left" else -120) * amount)

            self._with_modifiers(inp.get("text"), do)
        elif name == "type":
            self._type_text(inp.get("text", ""))
        elif name == "key":
            keys = _split_combo(inp.get("text", ""))
            if not keys:
                raise ActionError("key: tugma ko'rsatilmagan")
            for _ in range(max(1, min(int(inp.get("repeat", 1)), 100))):
                pyautogui.hotkey(*keys)
        elif name == "hold_key":
            keys = _split_combo(inp.get("text", ""))
            dur = min(float(inp.get("duration", 1)), 300)
            for k in keys:
                pyautogui.keyDown(k)
            try:
                time.sleep(dur)
            finally:
                for k in reversed(keys):
                    pyautogui.keyUp(k)
        elif name == "wait":
            time.sleep(min(float(inp.get("duration", 1)), 300))
        else:
            raise ActionError(f"Noma'lum amal: {name}")

        time.sleep(self.action_delay)
        return "OK"
