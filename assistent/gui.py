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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = load_config()
        self.tasks = load_tasks()
        self.events: queue.Queue = queue.Queue()
        self.chat_files: list[str] = []
        self.task_files: list[str] = []
        self.current_task_id: str | None = None
        self.worker: threading.Thread | None = None
        self.mini: tk.Toplevel | None = None

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

        self.root.after(100, self._poll_events)
        if not self.cfg.get("api_key"):
            self.nb.select(self.settings_tab)
            self._log("info", "Boshlash uchun 'Sozlamalar' bo'limida Anthropic API kalitini kiriting.")
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

    def run_task(self):
        if self._busy():
            return
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

        tips = ("Maslahatlar:\n"
                "• API kalitni console.anthropic.com → API Keys bo'limidan olasiz.\n"
                "• Favqulodda to'xtatish: sichqonchani ekranning chap-yuqori burchagiga olib boring.\n"
                "• Kichikroq skrinshot va 'low/medium' effort arzonroq ishlaydi.\n"
                f"• Sozlamalar va vazifalar saqlanadigan papka: {CONFIG_PATH.parent}")
        ttk.Label(tab, text=tips, foreground="#555", justify="left").grid(row=8, column=0, columnspan=3, sticky="w", pady=12)
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
            self._show_mini()
            self.root.withdraw()

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

    def stop(self):
        self.agent.stop_event.set()
        self.status.set("To'xtatilmoqda...")

    def _show_mini(self):
        m = tk.Toplevel(self.root)
        m.title("Assistent AI")
        m.attributes("-topmost", True)
        m.resizable(False, False)
        sw = m.winfo_screenwidth()
        m.geometry(f"320x90+{sw - 340}+10")
        self.mini_status = tk.StringVar(value="Ishlamoqda...")
        ttk.Label(m, textvariable=self.mini_status, wraplength=300).pack(fill="x", padx=8, pady=6)
        ttk.Button(m, text="■ To'xtatish", command=self.stop).pack(pady=(0, 6))
        m.protocol("WM_DELETE_WINDOW", self.stop)
        self.mini = m

    def _finish(self):
        if self.mini:
            self.mini.destroy()
            self.mini = None
        self.root.deiconify()
        self.root.lift()
        self.send_btn.configure(state="normal")
        self.run_task_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status.set("Tayyor")

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
                    if self.mini:
                        self.mini_status.set(text)
                else:
                    self._log(kind, text)
                    if self.mini and kind in ("action", "assistant", "error"):
                        self.mini_status.set(text[:120])
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
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
