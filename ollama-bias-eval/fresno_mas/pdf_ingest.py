"""Load one-page proposal PDFs (folder or a single multi-page file) for every agent."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .proposals import Proposal

COST_RE = re.compile(
    r"(?:cost|budget|request|ask|total)\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(million|m|k|thousand)?",
    re.I,
)
COST_RE_FALLBACK = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|m|k|thousand)?", re.I)
ID_RE = re.compile(r"\b(P\d{1,3}|PROP[-_]?\d{1,3}|PROPOSAL\s+\d{1,3})\b", re.I)


def _to_usd(num: str, unit: str | None) -> int:
    value = float(num.replace(",", ""))
    unit = (unit or "").lower()
    if unit in {"million", "m"}:
        value *= 1_000_000
    elif unit in {"k", "thousand"}:
        value *= 1_000
    return int(round(value))


def parse_cost(text: str) -> int | None:
    for cre in (COST_RE, COST_RE_FALLBACK):
        m = cre.search(text)
        if m:
            return _to_usd(m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None)
    return None


def infer_neighborhood(text: str) -> str:
    t = text.lower()
    votes = {
        "Southwest Fresno": len(re.findall(r"southwest|west fresno|\bsw\b", t)),
        "Central Fresno": len(re.findall(r"central|downtown|chinatown|tower district", t)),
        "Northeast Fresno": len(re.findall(r"northeast|\bne\b|woodward|copper river", t)),
        "Citywide": len(re.findall(r"citywide|city-wide|all three neighborhood", t)),
    }
    best = max(votes, key=votes.get)
    return best if votes[best] else "Citywide"


def extract_pdf_pages(path: Path) -> list[dict[str, Any]]:
    import fitz  # pymupdf

    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        pages.append(
            {
                "source_pdf": str(path),
                "source_page": i + 1,
                "text": text.strip(),
                "image_bytes": pix.tobytes("png"),
                "width": pix.width,
                "height": pix.height,
            }
        )
    doc.close()
    return pages


def render_page_pngs(pages: list[dict[str, Any]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, page in enumerate(pages, start=1):
        p = out_dir / f"proposal_page_{i:02d}.png"
        p.write_bytes(page["image_bytes"])
        paths.append(p)
    return paths


def _field(text: str, label: str) -> str | None:
    m = re.search(rf"{label}\s*[:\-]\s*(.+)", text, re.I)
    return m.group(1).strip() if m else None


def _block(text: str, label: str) -> str:
    nxt = r"what it is|who it helps|scalability|timeline|co-benefits|maintenance|id\b|cost\b"
    m = re.search(rf"{label}\s*:?\s*(.*?)(?=\n(?:{nxt})\b|\Z)", text, re.I | re.S)
    return (m.group(1).strip() if m else "")[:1800]


def page_to_proposal(page: dict[str, Any], index: int) -> Proposal:
    text = page.get("text") or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    pid_match = re.search(r"\b(P\d{2,3})\b", text)
    pid = pid_match.group(1).upper() if pid_match else f"P{index:02d}"
    title = None
    labeled = re.search(rf"{pid}\s*:\s*(.+)", text)
    if labeled:
        title = labeled.group(1).strip()[:180]
    if not title:
        title = _field(text, "title")
    if not title:
        title = next((ln for ln in lines if not ln.lower().startswith("city of fresno")), f"Untitled {index}")
        title = title[:180]
    neigh = _field(text, "neighborhood") or infer_neighborhood(text)
    cat = _field(text, "category") or "from_pdf"
    cost = parse_cost(text) or 0
    desc = _block(text, "what it is") or text[:1800]
    helps = _block(text, "who it helps") or ""
    return Proposal(
        id=pid,
        title=title,
        cost_usd=cost,
        neighborhood=neigh,
        category=cat,
        description=desc,
        who_it_helps=helps,
        scalability=_block(text, "scalability") or "",
        timeline=_field(text, "timeline") or "",
        cobenefits=_block(text, "co-benefits") or "",
        maintenance=_block(text, "maintenance") or "",
        raw_text=text,
        source_pdf=page.get("source_pdf", ""),
        source_page=page.get("source_page"),
    )


def collect_pdf_files(source: str | Path) -> list[Path]:
    path = Path(source)
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [path]
    if path.is_dir():
        return sorted(p for p in path.glob("**/*.pdf") if p.is_file())
    return []


def load_pages_from_source(source: str | Path) -> list[dict[str, Any]]:
    files = collect_pdf_files(source)
    pages: list[dict[str, Any]] = []
    for pdf in files:
        pages.extend(extract_pdf_pages(pdf))
    return pages


def proposals_from_pages(pages: Iterable[dict[str, Any]]) -> list[Proposal]:
    out = []
    seen = set()
    for i, page in enumerate(pages, start=1):
        p = page_to_proposal(page, i)
        if p.id in seen:
            p.id = f"{p.id}_{i:02d}"
        seen.add(p.id)
        out.append(p)
    return out


LLM_EXTRACT_PROMPT = """Extract a structured project proposal from this one-page summary.
Return JSON with keys:
id (string like P01), title, cost_usd (integer dollars, convert millions), 
neighborhood (Southwest Fresno | Central Fresno | Northeast Fresno | Citywide),
category, description, who_it_helps, scalability, timeline, cobenefits, maintenance.

PAGE TEXT:
{text}
"""


def structure_pages_with_llm(pages: list[dict[str, Any]], backend) -> list[Proposal]:
    """Optional second pass: use the 3B model to parse messy PDF text."""
    from .allocation import extract_json

    conversations = [
        [
            {
                "role": "system",
                "content": "You extract structured civic-project records. Reply with JSON only.",
            },
            {"role": "user", "content": LLM_EXTRACT_PROMPT.format(text=pg["text"][:6000])},
        ]
        for pg in pages
        if (pg.get("text") or "").strip()
    ]
    if not conversations:
        return proposals_from_pages(pages)
    texts = backend.chat_batch(conversations, json_mode=False)
    proposals = []
    for i, (page, raw) in enumerate(zip(pages, texts), start=1):
        data = extract_json(raw) or {}
        if not data:
            proposals.append(page_to_proposal(page, i))
            continue
        data.setdefault("id", f"P{i:02d}")
        data.setdefault("title", f"Proposal {i}")
        data.setdefault("cost_usd", parse_cost(page["text"]) or 0)
        data.setdefault("neighborhood", infer_neighborhood(page["text"]))
        data.setdefault("category", "from_pdf")
        data.setdefault("description", page["text"][:1800])
        p = Proposal.from_dict(data)
        p.raw_text = page["text"]
        p.source_pdf = page.get("source_pdf", "")
        p.source_page = page.get("source_page")
        proposals.append(p)
    return proposals


def load_proposals(
    source: str | Path | None = None,
    json_path: str | Path | None = None,
    use_sample_if_empty: bool = False,
    llm_backend=None,
    structure_with_llm: bool = False,
) -> tuple[list[Proposal], list[dict[str, Any]]]:
    """
    Returns (proposals, raw_pages).

    Drop PDFs in `proposals/` (one proposal per file, or one combined PDF).
    Sample catalog is never used unless use_sample_if_empty is explicitly True.
    """
    pages: list[dict[str, Any]] = []
    if source:
        pages = load_pages_from_source(source)
    if pages:
        if structure_with_llm and llm_backend is not None:
            proposals = structure_pages_with_llm(pages, llm_backend)
        else:
            proposals = proposals_from_pages(pages)
        return proposals, pages
    if json_path and Path(json_path).is_file():
        data = json.loads(Path(json_path).read_text())
        return [Proposal.from_dict(x) for x in data], []
    if use_sample_if_empty:
        from .sample_data import load_sample_proposals

        return load_sample_proposals(), []
    raise FileNotFoundError(
        f"No proposal PDFs found at {source}. "
        "Put a combined PDF or one-page PDFs in the proposals/ folder (or use the notebook uploader)."
    )


def save_notebook_uploads(uploads, dest: str | Path) -> list[Path]:
    """Save ipywidgets FileUpload payloads into proposals/."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    # widgets.FileUpload: dict-like (legacy) or tuple of UploadFile (ipywidgets 8)
    items = uploads.value if hasattr(uploads, "value") else uploads
    if isinstance(items, dict):
        iterable = items.items()
        for name, meta in iterable:
            data = meta["content"] if isinstance(meta, dict) else meta
            path = dest / name
            path.write_bytes(bytes(data))
            saved.append(path)
        return saved
    for item in items:
        name = getattr(item, "name", None) or item["name"]
        data = getattr(item, "content", None)
        if data is None:
            data = item["content"]
        path = dest / name
        path.write_bytes(bytes(data))
        saved.append(path)
    return saved


def write_sample_json(path: str | Path) -> Path:
    from .sample_data import load_sample_proposals

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [p.to_dict() for p in load_sample_proposals()]
    path.write_text(json.dumps(data, indent=2))
    return path
