"""Butun tizim bo'ylab ishlaydigan tezkor tugmalar (Windows).

Windows'ning RegisterHotKey funksiyasi ishlatiladi: tugmalar klaviatura tili
(lotin/kirill) qanday bo'lishidan qat'i nazar ishlaydi va boshqa dasturga
o'tib ketmaydi. Boshqa tizimlarda tezkor tugmalar o'chirilgan bo'ladi.
"""

import platform
import threading
from typing import Callable

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

_MODS = {"ctrl": MOD_CONTROL, "alt": MOD_ALT, "shift": MOD_SHIFT, "win": MOD_WIN}
_NAMED_VK = {f"f{i}": 0x6F + i for i in range(1, 13)}
_NAMED_VK.update({"space": 0x20, "pause": 0x13, "home": 0x24, "end": 0x23, "insert": 0x2D})


def parse(combo: str) -> tuple[int, int]:
    """'ctrl+alt+s' -> (modifiers, virtual key code)."""
    mods, vk = 0, None
    for part in combo.lower().replace(" ", "").split("+"):
        if part in _MODS:
            mods |= _MODS[part]
        elif part in _NAMED_VK:
            vk = _NAMED_VK[part]
        elif len(part) == 1 and part.isalnum():
            vk = ord(part.upper())
        else:
            raise ValueError(f"Noma'lum tugma: {part}")
    if vk is None:
        raise ValueError(f"Tugma ko'rsatilmagan: {combo}")
    return mods, vk


def pretty(combo: str) -> str:
    return "+".join(p.capitalize() if len(p) > 1 else p.upper() for p in combo.split("+"))


class HotkeyManager:
    """Tezkor tugmalarni ro'yxatdan o'tkazadi va bosilganda callback chaqiradi."""

    def __init__(self, bindings: dict[str, str], on_hotkey: Callable[[str], None],
                 on_error: Callable[[str], None]):
        self.bindings = bindings  # nom -> "ctrl+alt+s"
        self.on_hotkey = on_hotkey  # boshqa oqimdan chaqiriladi
        self.on_error = on_error
        self.thread: threading.Thread | None = None
        self.thread_id = None
        self.enabled = platform.system() == "Windows"

    def start(self):
        if not self.enabled:
            self.on_error("Tezkor tugmalar faqat Windows'da ishlaydi.")
            return
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.enabled and self.thread_id:
            import ctypes

            ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def _loop(self):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self.thread_id = kernel32.GetCurrentThreadId()

        ids = {}
        for i, (name, combo) in enumerate(self.bindings.items(), start=1):
            try:
                mods, vk = parse(combo)
            except ValueError as e:
                self.on_error(str(e))
                continue
            if user32.RegisterHotKey(None, i, mods | MOD_NOREPEAT, vk):
                ids[i] = name
            else:
                self.on_error(f"{pretty(combo)} tugmasini band qilib bo'lmadi (boshqa dastur ishlatayotgan "
                              "bo'lishi mumkin). config.json da boshqa tugma tanlang.")

        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam in ids:
                    try:
                        self.on_hotkey(ids[msg.wParam])
                    except Exception:  # noqa: BLE001
                        pass
        finally:
            for i in ids:
                user32.UnregisterHotKey(None, i)
