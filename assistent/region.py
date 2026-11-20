"""Maxfiylik chegarasi: ekranda to'rtburchak belgilash va uni chiziq bilan ko'rsatish."""

import tkinter as tk
from typing import Callable

BORDER_COLOR = "#ff2d2d"
BORDER_WIDTH = 4
MIN_SIZE = 80


def select_region(root: tk.Tk, mon: dict, current, on_done: Callable[[list | None], None]):
    """Butun ekranni xira qoplaydi; foydalanuvchi sichqoncha bilan to'rtburchak chizadi.

    on_done([x, y, w, h]) — monitorga nisbatan piksellarda, yoki bekor qilinsa None.
    """
    top = tk.Toplevel(root)
    top.overrideredirect(True)
    top.geometry(f"{mon['width']}x{mon['height']}+{mon['left']}+{mon['top']}")
    top.attributes("-topmost", True)
    try:
        top.attributes("-alpha", 0.35)
    except tk.TclError:
        pass
    cv = tk.Canvas(top, bg="black", highlightthickness=0, cursor="crosshair")
    cv.pack(fill="both", expand=True)
    cv.create_text(
        mon["width"] // 2, 60, fill="white", font=("Segoe UI", 20, "bold"),
        text=("AI ko'rishi mumkin bo'lgan joyni sichqoncha bilan to'rtburchak qilib belgilang.\n"
              "Enter — tasdiqlash   Esc — bekor qilish   Delete — chegarani olib tashlash"),
        justify="center",
    )
    state = {"start": None, "rect": None, "box": None}
    if current and len(current) == 4:
        x, y, w, h = current
        state["box"] = [x, y, w, h]
        state["rect"] = cv.create_rectangle(x, y, x + w, y + h, outline=BORDER_COLOR, width=3, fill="white")

    def finish(result):
        top.destroy()
        on_done(result)

    def press(e):
        state["start"] = (e.x, e.y)
        if state["rect"]:
            cv.delete(state["rect"])
        state["rect"] = cv.create_rectangle(e.x, e.y, e.x, e.y, outline=BORDER_COLOR, width=3, fill="white")

    def drag(e):
        if state["start"]:
            x0, y0 = state["start"]
            cv.coords(state["rect"], x0, y0, e.x, e.y)

    def release(e):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        x, y = min(x0, e.x), min(y0, e.y)
        w, h = abs(e.x - x0), abs(e.y - y0)
        state["start"] = None
        if w < MIN_SIZE or h < MIN_SIZE:
            cv.delete(state["rect"])
            state["rect"] = None
            state["box"] = None
            return
        state["box"] = [x, y, w, h]
        # Qo'yib yuborilganda darhol tasdiqlaymiz (eng oddiy yo'l).
        finish(state["box"])

    cv.bind("<ButtonPress-1>", press)
    cv.bind("<B1-Motion>", drag)
    cv.bind("<ButtonRelease-1>", release)
    top.bind("<Escape>", lambda e: finish("cancel"))
    top.bind("<Return>", lambda e: finish(state["box"] or "cancel"))
    top.bind("<Delete>", lambda e: finish(None))
    top.focus_force()
    top.grab_set()


class BorderOverlay:
    """Belgilangan maydon atrofida qizil chiziq (to'rtta ingichka oyna, maydon tashqarisida).

    Chiziq maydondan tashqarida turgani uchun AI ko'radigan rasmga tushmaydi.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.parts: list[tk.Toplevel] = []
        self._after = None

    def show(self, view: dict, mon: dict):
        self.hide()
        b = BORDER_WIDTH
        L, T = view["left"], view["top"]
        R, B = L + view["width"], T + view["height"]
        ml, mt = mon["left"], mon["top"]
        mr, mb = ml + mon["width"], mt + mon["height"]
        rects = [
            (max(ml, L - b), max(mt, T - b), min(mr, R + b), T),            # yuqori
            (max(ml, L - b), B, min(mr, R + b), min(mb, B + b)),            # pastki
            (max(ml, L - b), T, L, B),                                      # chap
            (R, T, min(mr, R + b), B),                                      # o'ng
        ]
        for x0, y0, x1, y1 in rects:
            if x1 - x0 < 1 or y1 - y0 < 1:
                continue  # chegara ekran chetiga tegib turgan bo'lsa
            w = tk.Toplevel(self.root)
            w.overrideredirect(True)
            w.attributes("-topmost", True)
            w.configure(bg=BORDER_COLOR)
            w.geometry(f"{x1 - x0}x{y1 - y0}+{x0}+{y0}")
            self.parts.append(w)
        self._keep_on_top()

    def _keep_on_top(self):
        if not self.parts:
            return
        for w in self.parts:
            try:
                w.lift()
                w.attributes("-topmost", True)
            except tk.TclError:
                pass
        self._after = self.root.after(2000, self._keep_on_top)

    def hide(self):
        if self._after:
            self.root.after_cancel(self._after)
            self._after = None
        for w in self.parts:
            try:
                w.destroy()
            except tk.TclError:
                pass
        self.parts = []
