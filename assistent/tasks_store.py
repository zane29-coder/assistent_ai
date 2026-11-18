"""Tezkor vazifalar (head prompt + fayllar) ro'yxatini saqlash."""

import json
import uuid

from .config import TASKS_PATH

SAMPLE_TASKS = [
    {
        "id": "sample-ref-fix",
        "name": "Google Sheets: #REF! xatolarini tuzatish",
        "prompt": (
            "Chrome'da ochiq turgan Google Sheets jadvalida #REF! xatolarini top va tuzat.\n"
            "Ish tartibi:\n"
            "1. Avval skrinshot olib, qaysi jadval ochiqligini aniqla. Agar Google Sheets ochiq bo'lmasa, to'xta va menga ayt.\n"
            "2. Ctrl+F (yoki Ctrl+H) bilan \"#REF!\" ni qidir; har bir topilgan katakni bosib, formulalar qatorida formulani o'qi.\n"
            "3. Formula nimaga ishora qilishi kerakligini atrofdagi ustun sarlavhalari va qo'shni kataklardagi "
            "o'xshash formulalardan aniqla va to'g'ri havolani qo'y.\n"
            "4. To'g'ri havolani aniq bilmasang, o'sha katakni o'zgartirma, ro'yxatga yozib qo'y.\n"
            "5. Oxirida qaysi kataklarni qanday tuzatganing va qaysilarini tuzatmaganingni qisqa ro'yxat qilib ber."
        ),
        "files": [],
    },
]


def load_tasks() -> list[dict]:
    if TASKS_PATH.exists():
        try:
            data = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    save_tasks(SAMPLE_TASKS)
    return [dict(t) for t in SAMPLE_TASKS]


def save_tasks(tasks: list[dict]) -> None:
    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def new_task(name: str, prompt: str, files: list[str]) -> dict:
    return {"id": uuid.uuid4().hex[:10], "name": name, "prompt": prompt, "files": list(files)}
