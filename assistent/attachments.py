"""Biriktirilgan fayllarni Claude'ga yuboriladigan bloklarga aylantirish."""

import base64
import io
from pathlib import Path

from PIL import Image

IMAGE_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".gif": "image/gif", ".webp": "image/webp"}
TEXT_EXT = {".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm", ".log",
            ".py", ".js", ".ts", ".css", ".sql", ".yaml", ".yml", ".ini", ".bat"}
MAX_TEXT_CHARS = 300_000
MAX_PDF_BYTES = 30 * 1024 * 1024


class AttachmentError(Exception):
    pass


def _image_block(path: Path) -> dict:
    img = Image.open(path)
    img.load()
    w, h = img.size
    s = min(1.0, 2000 / max(w, h))
    if s < 1.0:
        img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": base64.b64encode(buf.getvalue()).decode("ascii")}}


def _xlsx_text(path: Path) -> str:
    import openpyxl

    # data_only=False: formulalarni (masalan =VLOOKUP(#REF!...)) ko'rish uchun.
    wb = openpyxl.load_workbook(path, data_only=False, read_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"### Varaq: {ws.title}")
        for row in ws.iter_rows():
            cells = []
            for c in row:
                if c.value is not None and hasattr(c, "coordinate"):
                    cells.append(f"{c.coordinate}={c.value}")
            if cells:
                out.append(" | ".join(cells))
    return "\n".join(out)


def file_to_blocks(path_str: str) -> list[dict]:
    path = Path(path_str)
    if not path.exists():
        raise AttachmentError(f"Fayl topilmadi: {path}")
    ext = path.suffix.lower()
    header = {"type": "text", "text": f"[Biriktirilgan fayl: {path.name}]"}

    if ext in IMAGE_EXT:
        return [header, _image_block(path)]
    if ext == ".pdf":
        data = path.read_bytes()
        if len(data) > MAX_PDF_BYTES:
            raise AttachmentError(f"{path.name}: PDF juda katta (30 MB dan oshmasin)")
        return [{"type": "document", "title": path.name,
                 "source": {"type": "base64", "media_type": "application/pdf",
                            "data": base64.b64encode(data).decode("ascii")}}]
    if ext in (".xlsx", ".xlsm"):
        text = _xlsx_text(path)
    elif ext in TEXT_EXT:
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        # Boshqa turdagi fayl: faqat yo'lini aytamiz, Claude kerak bo'lsa ekranda ochadi.
        return [{"type": "text", "text": f"[Biriktirilgan fayl: {path.name}, joylashuvi: {path}. "
                                         "Bu turdagi faylning ichini yubora olmayman; kerak bo'lsa ekranda oching.]"}]

    if len(text) > MAX_TEXT_CHARS:
        raise AttachmentError(f"{path.name}: matn juda uzun ({len(text)} belgi). "
                              f"{MAX_TEXT_CHARS} belgidan kichik fayl biriktiring yoki bo'lib yuboring.")
    return [{"type": "text", "text": f"[Biriktirilgan fayl: {path.name}]\n```\n{text}\n```"}]


def files_to_blocks(paths: list[str]) -> list[dict]:
    blocks: list[dict] = []
    for p in paths:
        blocks.extend(file_to_blocks(p))
    return blocks
