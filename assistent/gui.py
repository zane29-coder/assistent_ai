"""Asosiy oyna: Chat, Tezkor vazifalar va Sozlamalar."""

import queue
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

from .attachments import AttachmentError, files_to_blocks
from .config import CONFIG_PATH, load_config, save_config
from .tasks_store import load_tasks, new_task, save_tasks

MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
EFFORTS = ["low", "medium", "high", "xhigh", "max"]
API_KEYS_URL = "https://console.anthropic.com/settings/keys"
HOTKEY_DEFAULTS = {
    "start": "ctrl+alt+s",
    "pause": "ctrl+alt+p",
    "screenshot": "ctrl+alt+r",
    "stop": "ctrl+alt+x",
    "region": "ctrl+alt+l",
}


def _beep(kind: str):
    """Oyna yashiringanda ham nima bo'lganini eshitib turish uchun qisqa ovoz."""
    try:
        import winsound

        tones = {"start": [(880, 90)], "done": [(660, 90), (880, 120)], "pause": [(440, 150)],
                 "resume": [(660, 90)], "error": [(220, 200)]}
        for freq, ms in tones.get(kind, []):
            winsound.Beep(freq, ms)
    except Exception:  # noqa: BLE001
        pass


class App:
    def __init__(self, root: tk.Tk, selftest: bool = False):
        self.root = root
        self.cfg = load_config()
        self.tasks = load_tasks()
        self.events: queue.Queue = queue.Queue()
        self.chat_files: list[str] = []
        self.task_files: list[str] = []
        self.current_task_id: str | None = None
        self.worker: threading.Thread | None = None

        from .agent import Agent  # og'ir kutubxonalar oyna ochilgandan keyin

        self.agent = Agent(self.cfg, self._log_from_thread)

        root.title("Assistent AI — ekranni boshqaruvchi yordamchi")
        root.geometry("980x700")
        root.minsize(760, 520)

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)
        self._build_chat_tab()
        self._build_tasks_tab()
        self._build_settings_tab()

        self.status = tk.StringVar(value="Tayyor")
        bar = ttk.Frame(root)
        bar.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(bar, textvariable=self.status).pack(side="left")
        self.cost_var = tk.StringVar(value="Sarflangan: $0.000")
        ttk.Label(bar, textvariable=self.cost_var).pack(side="right")
        ttk.Label(root, text="Tezkor tugmalar:  " + self._hotkey_text(), foreground="#555",
                  wraplength=940, justify="left").pack(fill="x", padx=8, pady=(0, 6))

        from .region import BorderOverlay

        self._selecting = False
        self.border = BorderOverlay(root)
        self._apply_region()
        self._start_hotkeys()
        self.root.after(100, self._poll_events)
        if not self.cfg.get("api_key"):
            self.nb.select(self.settings_tab)
            self._log("info", "Boshlash uchun 'Sozlamalar' bo'limida Anthropic API kalitini kiriting.")
            if not selftest:
                self.root.after(400, self._welcome)

    def _welcome(self):
        if messagebox.askyesno(
            "Xush kelibsiz!",
            "Dastur ishlashi uchun bitta narsa kerak: Anthropic API kalit.\n\n"
            "1. Hozir ochiladigan saytda ro'yxatdan o'ting.\n"
            "2. Billing bo'limida balansni to'ldiring (masalan $5).\n"
            "3. API Keys → Create Key, kalitni nusxalang.\n"
            "4. Kalitni shu dasturdagi 'Anthropic API kalit' maydoniga qo'yib, 'Saqlash'ni bosing.\n\n"
            "Saytni hozir ochaymi?",
        ):
            webbrowser.open(API_KEYS_URL)
            self.key_entry.focus_set()

    # ------------------------------------------------------------------ Chat
    def _build_chat_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Chat  ")
        self.chat_tab = tab

        self.log_box = ScrolledText(tab, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.log_box.pack(fill="both", expand=True, padx=4, pady=4)
        for tag, color in {"user": "#1a4fa0", "assistant": "#111111", "thinking": "#888888",
                           "action": "#2e7d32", "info": "#6a1b9a", "error": "#c62828"}.items():
            self.log_box.tag_configure(tag, foreground=color)
        self.log_box.tag_configure("label", font=("Segoe UI", 10, "bold"))

        bottom = ttk.Frame(tab)
        bottom.pack(fill="x", padx=4, pady=4)
        self.input = tk.Text(bottom, height=4, wrap="word", font=("Segoe UI", 10))
        self.input.pack(side="left", fill="x", expand=True)
        self.input.bind("<Control-Return>", lambda e: (self.send_chat(), "break")[1])

        btns = ttk.Frame(bottom)
        btns.pack(side="right", padx=(6, 0))
        self.send_btn = ttk.Button(btns, text="Yuborish (Ctrl+Enter)", command=self.send_chat)
        self.send_btn.pack(fill="x")
        ttk.Button(btns, text="Fayl biriktirish", command=self.attach_chat_file).pack(fill="x", pady=2)
        self.stop_btn = ttk.Button(btns, text="■ To'xtatish", command=self.stop, state="disabled")
        self.stop_btn.pack(fill="x")
        ttk.Button(btns, text="Yangi suhbat", command=self.new_chat).pack(fill="x", pady=(2, 0))

        self.chat_files_var = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.chat_files_var, foreground="#555").pack(fill="x", padx=6)

    def attach_chat_file(self):
        paths = filedialog.askopenfilenames(title="Fayl tanlang")
        if paths:
            self.chat_files.extend(paths)
            self._refresh_chat_files()

    def _refresh_chat_files(self):
        if self.chat_files:
            names = ", ".join(Path(p).name for p in self.chat_files)
            self.chat_files_var.set(f"Biriktirilgan: {names}   (yuborilgandan keyin tozalanadi)")
        else:
            self.chat_files_var.set("")

    def send_chat(self):
        text = self.input.get("1.0", "end").strip()
        if not text and not self.chat_files:
            return
        try:
            content = files_to_blocks(self.chat_files)
        except AttachmentError as e:
            messagebox.showerror("Fayl xatosi", str(e))
            return
        if text:
            content.append({"type": "text", "text": text})
        shown = text + (f"\n[fayllar: {', '.join(Path(p).name for p in self.chat_files)}]" if self.chat_files else "")
        self.input.delete("1.0", "end")
        self.chat_files = []
        self._refresh_chat_files()
        self._start(content, shown)

    def new_chat(self):
        if self._busy():
            return
        self.agent.reset()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._log("info", "Yangi suhbat boshlandi.")

    # ---------------------------------------------------------- Quick tasks
    def _build_tasks_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Tezkor vazifalar  ")

        left = ttk.Frame(tab)
        left.pack(side="left", fill="y", padx=4, pady=4)
        ttk.Label(left, text="Saqlangan vazifalar").pack(anchor="w")
        self.task_list = tk.Listbox(left, width=34, height=20, exportselection=False)
        self.task_list.pack(fill="y", expand=True)
        self.task_list.bind("<<ListboxSelect>>", lambda e: self._select_task())
        self.task_list.bind("<Double-Button-1>", lambda e: self.run_task())
        ttk.Button(left, text="+ Yangi vazifa", command=self.new_task).pack(fill="x", pady=(4, 0))

        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        ttk.Label(right, text="Nomi").pack(anchor="w")
        self.task_name = ttk.Entry(right)
        self.task_name.pack(fill="x")
        ttk.Label(right, text="Head prompt (vazifa ko'rsatmasi)").pack(anchor="w", pady=(6, 0))
        self.task_prompt = ScrolledText(right, height=12, wrap="word", font=("Segoe UI", 10))
        self.task_prompt.pack(fill="both", expand=True)

        ttk.Label(right, text="Biriktirilgan fayllar (har safar vazifa bilan birga yuboriladi)").pack(anchor="w", pady=(6, 0))
        files_row = ttk.Frame(right)
        files_row.pack(fill="x")
        self.task_files_list = tk.Listbox(files_row, height=4)
        self.task_files_list.pack(side="left", fill="x", expand=True)
        fbtn = ttk.Frame(files_row)
        fbtn.pack(side="left", padx=4)
        ttk.Button(fbtn, text="Qo'shish", command=self.add_task_file).pack(fill="x")
        ttk.Button(fbtn, text="Olib tashlash", command=self.remove_task_file).pack(fill="x", pady=2)

        ttk.Label(right, text="Bu safar uchun qo'shimcha izoh (ixtiyoriy)").pack(anchor="w", pady=(6, 0))
        self.task_extra = ttk.Entry(right)
        self.task_extra.pack(fill="x")

        actions = ttk.Frame(right)
        actions.pack(fill="x", pady=6)
        self.run_task_btn = ttk.Button(actions, text="▶ Ishga tushirish", command=self.run_task)
        self.run_task_btn.pack(side="left")
        ttk.Button(actions, text="Saqlash", command=self.save_task).pack(side="left", padx=6)
        ttk.Button(actions, text="O'chirish", command=self.delete_task).pack(side="left")

        self._refresh_task_list()
        if self.tasks:
            self.task_list.selection_set(0)
            self._select_task()

    def _refresh_task_list(self):
        self.task_list.delete(0, "end")
        for t in self.tasks:
            self.task_list.insert("end", t["name"])

    def _select_task(self):
        sel = self.task_list.curselection()
        if not sel:
            return
        t = self.tasks[sel[0]]
        self.current_task_id = t["id"]
        self.task_name.delete(0, "end")
        self.task_name.insert(0, t["name"])
        self.task_prompt.delete("1.0", "end")
        self.task_prompt.insert("1.0", t["prompt"])
        self.task_files = list(t.get("files", []))
        self._refresh_task_files()

    def _refresh_task_files(self):
        self.task_files_list.delete(0, "end")
        for p in self.task_files:
            self.task_files_list.insert("end", p)

    def add_task_file(self):
        paths = filedialog.askopenfilenames(title="Fayl tanlang")
        if paths:
            self.task_files.extend(paths)
            self._refresh_task_files()

    def remove_task_file(self):
        sel = self.task_files_list.curselection()
        if sel:
            del self.task_files[sel[0]]
            self._refresh_task_files()

    def new_task(self):
        self.current_task_id = None
        self.task_list.selection_clear(0, "end")
        self.task_name.delete(0, "end")
        self.task_prompt.delete("1.0", "end")
        self.task_files = []
        self._refresh_task_files()
        self.task_name.focus_set()

    def save_task(self) -> dict | None:
        name = self.task_name.get().strip()
        prompt = self.task_prompt.get("1.0", "end").strip()
        if not name or not prompt:
            messagebox.showwarning("Vazifa", "Nomi va head prompt bo'sh bo'lmasin.")
            return None
        task = next((t for t in self.tasks if t["id"] == self.current_task_id), None)
        if task:
            task.update(name=name, prompt=prompt, files=list(self.task_files))
        else:
            task = new_task(name, prompt, self.task_files)
            self.tasks.append(task)
            self.current_task_id = task["id"]
        save_tasks(self.tasks)
        self._refresh_task_list()
        idx = self.tasks.index(task)
        self.task_list.selection_set(idx)
        self.status.set(f"Saqlandi: {name}")
        return task

    def delete_task(self):
        task = next((t for t in self.tasks if t["id"] == self.current_task_id), None)
        if task and messagebox.askyesno("O'chirish", f"'{task['name']}' vazifasini o'chiraymi?"):
            self.tasks.remove(task)
            save_tasks(self.tasks)
            self._refresh_task_list()
            self.new_task()

    def run_task(self, from_hotkey: bool = False):
        if self._busy():
            return
        if from_hotkey and not self.task_name.get().strip() and self.tasks:
            self.task_list.selection_clear(0, "end")
            self.task_list.selection_set(0)
            self._select_task()
        task = self.save_task()
        if not task:
            return
        try:
            content = files_to_blocks(task.get("files", []))
        except AttachmentError as e:
            messagebox.showerror("Fayl xatosi", str(e))
            return
        text = f"Tezkor vazifa: {task['name']}\n\n{task['prompt']}"
        extra = self.task_extra.get().strip()
        if extra:
            text += f"\n\nQo'shimcha izoh: {extra}"
        content.append({"type": "text", "text": text})
        # Har bir tezkor vazifa yangi suhbatda boshlanadi; keyin Chat'da davom ettirish mumkin.
        self.agent.reset()
        self.nb.select(self.chat_tab)
        self._log("info", f"— Tezkor vazifa: {task['name']} —")
        self._start(content, text if not task.get("files") else text + f"\n[fayllar: {len(task['files'])} ta]")

    # ------------------------------------------------------------- Settings
    def _build_settings_tab(self):
        tab = ttk.Frame(self.nb, padding=12)
        self.nb.add(tab, text="  Sozlamalar  ")
        self.settings_tab = tab

        ttk.Label(tab, text="Anthropic API kalit").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value=self.cfg.get("api_key", ""))
        self.key_entry = ttk.Entry(tab, textvariable=self.key_var, show="•", width=60)
        self.key_entry.grid(row=0, column=1, sticky="we", pady=3)
        self.show_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Ko'rsatish", variable=self.show_key,
                        command=lambda: self.key_entry.configure(show="" if self.show_key.get() else "•")
                        ).grid(row=0, column=2, padx=6)

        ttk.Label(tab, text="Model").grid(row=1, column=0, sticky="w")
        self.model_var = tk.StringVar(value=self.cfg.get("model"))
        ttk.Combobox(tab, textvariable=self.model_var, values=MODELS, width=30).grid(row=1, column=1, sticky="w", pady=3)

        ttk.Label(tab, text="Fikrlash darajasi (effort)").grid(row=2, column=0, sticky="w")
        self.effort_var = tk.StringVar(value=self.cfg.get("effort"))
        ttk.Combobox(tab, textvariable=self.effort_var, values=EFFORTS, state="readonly", width=12).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(tab, text="Bitta vazifada eng ko'p qadam").grid(row=3, column=0, sticky="w")
        self.steps_var = tk.IntVar(value=self.cfg.get("max_steps"))
        ttk.Spinbox(tab, from_=5, to=300, textvariable=self.steps_var, width=8).grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(tab, text="Skrinshot o'lchami (uzun tomoni, px)").grid(row=4, column=0, sticky="w")
        self.edge_var = tk.IntVar(value=self.cfg.get("screenshot_long_edge"))
        ttk.Spinbox(tab, from_=800, to=2576, increment=100, textvariable=self.edge_var, width=8).grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(tab, text="Amallar orasidagi kutish (soniya)").grid(row=5, column=0, sticky="w")
        self.delay_var = tk.DoubleVar(value=self.cfg.get("action_delay"))
        ttk.Spinbox(tab, from_=0.0, to=3.0, increment=0.1, textvariable=self.delay_var, width=8).grid(row=5, column=1, sticky="w", pady=3)

        self.hide_var = tk.BooleanVar(value=self.cfg.get("hide_window_while_running"))
        ttk.Checkbutton(tab, text="Vazifa ishlayotganda bu oynani yashirish (tavsiya etiladi)",
                        variable=self.hide_var).grid(row=6, column=1, sticky="w", pady=6)

        row = ttk.Frame(tab)
        row.grid(row=7, column=1, sticky="w", pady=8)
        ttk.Button(row, text="Saqlash", command=self.save_settings).pack(side="left")
        ttk.Button(row, text="API kalitni tekshirish", command=self.test_key).pack(side="left", padx=6)
        ttk.Button(row, text="API kalit olish (sayt)", command=lambda: webbrowser.open(API_KEYS_URL)).pack(side="left")

        reg = ttk.LabelFrame(tab, text="Maxfiylik chegarasi (Ctrl+Alt+L)", padding=8)
        reg.grid(row=8, column=0, columnspan=3, sticky="we", pady=(4, 0))
        self.region_var = tk.StringVar(value="")
        ttk.Label(reg, text="AI faqat belgilangan to'rtburchak ichini ko'radi va sichqonchani faqat shu yerda "
                            "boshqaradi. Tashqaridagi hech narsa unga yuborilmaydi.",
                  wraplength=700, justify="left").pack(anchor="w")
        ttk.Label(reg, textvariable=self.region_var, foreground="#1a4fa0").pack(anchor="w", pady=4)
        rrow = ttk.Frame(reg)
        rrow.pack(anchor="w")
        ttk.Button(rrow, text="Chegarani belgilash", command=self.choose_region).pack(side="left")
        ttk.Button(rrow, text="Olib tashlash", command=self.clear_region).pack(side="left", padx=6)

        tips = ("Maslahatlar:\n"
                "• API kalitni console.anthropic.com → API Keys bo'limidan olasiz.\n"
                "• Favqulodda to'xtatish: Ctrl+Alt+X yoki sichqonchani ekranning chap-yuqori burchagiga olib boring.\n"
                "• Tezkor tugmalarni config.json dagi hotkey_start, hotkey_pause, hotkey_screenshot, hotkey_stop, hotkey_region orqali o'zgartirish mumkin.\n"
                "• Kichikroq skrinshot va 'low/medium' effort arzonroq ishlaydi.\n"
                f"• Sozlamalar va vazifalar saqlanadigan papka: {CONFIG_PATH.parent}")
        ttk.Label(tab, text=tips, foreground="#555", justify="left").grid(row=9, column=0, columnspan=3, sticky="w", pady=12)
        tab.columnconfigure(1, weight=1)

    def save_settings(self):
        try:
            self.cfg.update(
                api_key=self.key_var.get().strip(),
                model=self.model_var.get().strip() or "claude-opus-5-5",
                effort=self.effort_var.get(),
                max_steps=int(self.steps_var.get()),
                screenshot_long_edge=int(self.edge_var.get()),
                action_delay=float(self.delay_var.get()),
                hide_window_while_running=bool(self.hide_var.get()),
            )
        except (tk.TclError, ValueError):
            messagebox.showerror("Sozlamalar", "Raqamli maydonlarni to'g'ri kiriting.")
            return
        save_config(self.cfg)
        self.status.set("Sozlamalar saqlandi")

    def test_key(self):
        self.save_settings()
        import anthropic

        try:
            m = anthropic.Anthropic(api_key=self.cfg["api_key"]).models.retrieve(self.cfg["model"])
            messagebox.showinfo("API kalit", f"Kalit ishlayapti. Model: {m.display_name}")
        except anthropic.AuthenticationError:
            messagebox.showerror("API kalit", "Kalit noto'g'ri.")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("API kalit", f"Tekshirib bo'lmadi: {e}")

    # -------------------------------------------------------------- Running
    def _busy(self) -> bool:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Band", "Hozir vazifa bajarilmoqda. Avval tugashini kuting yoki to'xtating.")
            return True
        return False

    def _start(self, content: list[dict], shown_text: str):
        if self._busy():
            return
        self.save_settings()
        self._log("user", shown_text)
        self.send_btn.configure(state="disabled")
        self.run_task_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        if self.cfg.get("hide_window_while_running"):
            self.root.withdraw()
        _beep("start")

        def work():
            try:
                time.sleep(0.6)  # oyna yashirilishini kutamiz
                self.agent.run(content)
            except Exception as e:  # noqa: BLE001
                self.events.put(("error", str(e)))
            finally:
                self.events.put(("done", ""))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def _running(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def stop(self):
        self.agent.pause_event.clear()
        self.agent.stop_event.set()
        self.status.set("To'xtatilmoqda...")

    def _finish(self):
        self.root.deiconify()
        self.root.lift()
        self.send_btn.configure(state="normal")
        self.run_task_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status.set("Tayyor")
        _beep("done")

    # ------------------------------------------------------ Privacy region
    def choose_region(self):
        if self._running() or self._selecting:
            return
        from .computer import primary_monitor
        from .region import select_region

        self._selecting = True
        was_visible = self.root.state() != "withdrawn"
        self.border.hide()
        self.root.withdraw()

        def done(result):
            self._selecting = False
            if result != "cancel":
                self.cfg["privacy_region"] = result
                save_config(self.cfg)
            self._apply_region()
            if was_visible:
                self.root.deiconify()
            if result == "cancel":
                return
            if result:
                self._log("info", "Maxfiylik chegarasi o'rnatildi. AI endi faqat qizil chiziq ichini ko'radi.")
            else:
                self._log("info", "Maxfiylik chegarasi olib tashlandi. AI butun ekranni ko'radi.")
            _beep("resume")

        # Oyna yashirilishiga ulgurishi uchun biroz kutamiz.
        self.root.after(250, lambda: select_region(self.root, primary_monitor(),
                                                   self.cfg.get("privacy_region"), done))

    def clear_region(self):
        if self._running():
            return
        self.cfg["privacy_region"] = None
        save_config(self.cfg)
        self._apply_region()
        self._log("info", "Maxfiylik chegarasi olib tashlandi. AI butun ekranni ko'radi.")

    def _apply_region(self):
        """Saqlangan chegarani ekranda qizil chiziq bilan ko'rsatadi."""
        from .computer import primary_monitor, region_to_view

        mon = primary_monitor()
        view = region_to_view(self.cfg.get("privacy_region"), mon)
        if view:
            self.border.show(view, mon)
            self.region_var.set(f"Yoqilgan: {view['width']}x{view['height']} px "
                                f"(chap-yuqori burchagi {view['left']}, {view['top']})")
        else:
            self.border.hide()
            self.region_var.set("O'chirilgan — AI butun ekranni ko'radi")

    # ------------------------------------------------------------- Hotkeys
    def _start_hotkeys(self):
        from .hotkeys import HotkeyManager

        bindings = {name: self.cfg.get(f"hotkey_{name}", default)
                    for name, default in HOTKEY_DEFAULTS.items()}
        self.hotkeys = HotkeyManager(
            bindings,
            on_hotkey=lambda name: self.events.put(("hotkey", name)),
            on_error=lambda msg: self.events.put(("error", msg)),
        )
        self.hotkeys.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.agent.stop_event.set()
        self.hotkeys.stop()
        self.border.hide()
        self.root.destroy()

    def _hotkey_text(self) -> str:
        from .hotkeys import pretty

        labels = {"start": "tanlangan tezkor vazifani boshlash",
                  "pause": "pauza / davom ettirish",
                  "screenshot": "yangi ekran rasmini yuborish",
                  "stop": "to'xtatish",
                  "region": "AI ko'radigan joyni belgilash"}
        return "   ".join(f"{pretty(self.cfg.get(f'hotkey_{n}', d))} — {labels[n]}"
                          for n, d in HOTKEY_DEFAULTS.items())

    def _on_hotkey(self, name: str):
        running = self._running()
        if name == "start":
            if running:
                _beep("error")
            else:
                self.run_task(from_hotkey=True)
        elif name == "pause":
            if not running:
                _beep("error")
                return
            paused = self.agent.toggle_pause()
            self.status.set("Pauza" if paused else "Davom etmoqda...")
            _beep("pause" if paused else "resume")
        elif name == "screenshot":
            if running:
                self.agent.fresh_shot.set()
                if self.agent.pause_event.is_set():
                    self.agent.toggle_pause()  # yangi rasm bilan davom ettiramiz
                _beep("resume")
            else:
                self._attach_screenshot_to_chat()
        elif name == "stop":
            if running:
                self.stop()
                _beep("pause")
        elif name == "region":
            if running:
                _beep("error")
            else:
                self.choose_region()

    def _attach_screenshot_to_chat(self):
        """Vazifa ishlamayotganda: hozirgi ekranni chatga biriktirib, oynani ochadi."""
        import tempfile

        from .computer import Computer

        try:
            block = Computer(self.cfg.get("screenshot_long_edge", 1366),
                             region=self.cfg.get("privacy_region")).screenshot_block()
            import base64

            path = Path(tempfile.gettempdir()) / f"assistent_ekran_{int(time.time())}.png"
            path.write_bytes(base64.b64decode(block["source"]["data"]))
        except Exception as e:  # noqa: BLE001
            self._log("error", f"Skrinshot olinmadi: {e}")
            return
        self.chat_files.append(str(path))
        self._refresh_chat_files()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.nb.select(self.chat_tab)
        self.input.focus_set()
        _beep("resume")

    # ------------------------------------------------------------- Logging
    def _log_from_thread(self, kind: str, text: str):
        self.events.put((kind, text))

    def _poll_events(self):
        try:
            while True:
                kind, text = self.events.get_nowait()
                if kind == "done":
                    self._finish()
                elif kind == "status":
                    self.status.set(text)
                elif kind == "hotkey":
                    self._on_hotkey(text)
                else:
                    self._log(kind, text)
                self.cost_var.set(f"Sarflangan: ${self.agent.cost_usd():.3f}")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _log(self, kind: str, text: str):
        labels = {"user": "Siz", "assistant": "Claude", "thinking": "Fikr", "action": "Amal",
                  "info": "Info", "error": "Xato"}
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{labels.get(kind, kind)}: ", ("label", kind))
        self.log_box.insert("end", text.strip() + "\n\n", kind)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")


def main():
    from . import computer  # noqa: F401  (Windows DPI sozlamasi Tk oynasidan oldin o'rnatilishi kerak)

    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
