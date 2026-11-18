"""Biriktirilgan fayllarni Claude'ga yuboriladigan bloklarga aylantirish.

Fayl ichidagi ma'lumot to'g'ridan-to'g'ri suhbatga qo'shiladi, shuning uchun
Claude faylni kompyuterda ochmasdan o'zi tahlil qiladi.
"""

import base64
import io
from pathlib import Path

from PIL import Image

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
TEXT_EXT = {".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm", ".log",
            ".py", ".js", ".ts", ".css", ".sql", ".yaml", ".yml", ".ini", ".bat", ".rtf"}
MAX_TEXT_CHARS = 300_000
MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_ROWS_PER_SHEET = 5000


class AttachmentError(Exception):
    pass


def _header(name: str) -> str:
    return (f"[Biriktirilgan fayl: {name}. Faylning mazmuni shu yerda berilgan — "
            "uni kompyuterda ochish yoki qidirish shart emas.]")


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

    # Formulalar (masalan =VLOOKUP(#REF!...)) va ularning oxirgi hisoblangan qiymatlari.
    wb_f = openpyxl.load_workbook(path, data_only=False, read_only=True)
    wb_v = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = []
    for ws_f, ws_v in zip(wb_f.worksheets, wb_v.worksheets):
        out.append(f"### Varaq: {ws_f.title}")
        for i, (row_f, row_v) in enumerate(zip(ws_f.iter_rows(), ws_v.iter_rows())):
            if i >= MAX_ROWS_PER_SHEET:
                out.append(f"... (varaqda {MAX_ROWS_PER_SHEET} qatordan ko'p, qolgani yuborilmadi)")
                break
            cells = []
            for cf, cv in zip(row_f, row_v):
                if cf.value is None or not hasattr(cf, "coordinate"):
                    continue
                if isinstance(cf.value, str) and cf.value.startswith("="):
                    shown = f" → {cv.value}" if cv.value is not None else ""
                    cells.append(f"{cf.coordinate}: {cf.value}{shown}")
                else:
                    cells.append(f"{cf.coordinate}: {cf.value}")
            if cells:
                out.append(" | ".join(cells))
    return "\n".join(out)


def _xls_text(path: Path) -> str:
    import xlrd

    book = xlrd.open_workbook(str(path))
    out = []
    for sh in book.sheets():
        out.append(f"### Varaq: {sh.name}")
        for r in range(min(sh.nrows, MAX_ROWS_PER_SHEET)):
            vals = [str(v) for v in sh.row_values(r)]
            if any(vals):
                out.append(" | ".join(vals))
    return "\n".join(out)


def _docx_text(path: Path) -> str:
    import docx

    d = docx.Document(str(path))
    out = [p.text for p in d.paragraphs if p.text.strip()]
    for ti, table in enumerate(d.tables, 1):
        out.append(f"### Jadval {ti}")
        for row in table.rows:
            out.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(out)


def _pptx_text(path: Path) -> str:
    from pptx import Presentation

    prs = Presentation(str(path))
    out = []
    for i, slide in enumerate(prs.slides, 1):
        out.append(f"### Slayd {i}")
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                out.append(shape.text_frame.text)
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    out.append(" | ".join(c.text for c in row.cells))
    return "\n".join(out)


def _read_text_any(path: Path) -> str | None:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-16", "cp1251"):
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        # Ikkilik (binary) fayllarni matn deb adashtirmaslik uchun.
        if text and sum(ch.isprintable() or ch in "\r\n\t" for ch in text[:5000]) / min(len(text), 5000) > 0.9:
            return text
    return None


def file_to_blocks(path_str: str) -> list[dict]:
    path = Path(path_str)
    if not path.exists():
        raise AttachmentError(f"Fayl topilmadi: {path}")
    ext = path.suffix.lower()

    if ext in IMAGE_EXT:
        return [{"type": "text", "text": _header(path.name)}, _image_block(path)]
    if ext == ".pdf":
        data = path.read_bytes()
        if len(data) > MAX_PDF_BYTES:
            raise AttachmentError(f"{path.name}: PDF juda katta (30 MB dan oshmasin)")
        return [{"type": "text", "text": _header(path.name)},
                {"type": "document", "title": path.name,
                 "source": {"type": "base64", "media_type": "application/pdf",
                            "data": base64.b64encode(data).decode("ascii")}}]

    try:
        if ext in (".xlsx", ".xlsm"):
            text = _xlsx_text(path)
        elif ext == ".xls":
            text = _xls_text(path)
        elif ext == ".docx":
            text = _docx_text(path)
        elif ext == ".pptx":
            text = _pptx_text(path)
        elif ext in TEXT_EXT:
            text = path.read_text(encoding="utf-8", errors="replace")
        else:
            text = _read_text_any(path)
    except AttachmentError:
        raise
    except Exception as e:  # noqa: BLE001
        raise AttachmentError(f"{path.name} faylini o'qib bo'lmadi: {e}")

    if text is None:
        raise AttachmentError(
            f"{path.name}: bu turdagi faylni o'qiy olmayman. Word (.docx), Excel (.xlsx, .xls, .csv), "
            "PowerPoint (.pptx), PDF, rasm yoki matnli fayl biriktiring. Eski .doc faylni Word'da "
            ".docx qilib saqlab oling.")
    if len(text) > MAX_TEXT_CHARS:
        raise AttachmentError(f"{path.name}: matn juda uzun ({len(text)} belgi). "
                              f"{MAX_TEXT_CHARS} belgidan kichik fayl biriktiring yoki bo'lib yuboring.")
    return [{"type": "text", "text": f"{_header(path.name)}\n```\n{text}\n```"}]


def files_to_blocks(paths: list[str]) -> list[dict]:
    blocks: list[dict] = []
    for p in paths:
        blocks.extend(file_to_blocks(p))
    return blocks
