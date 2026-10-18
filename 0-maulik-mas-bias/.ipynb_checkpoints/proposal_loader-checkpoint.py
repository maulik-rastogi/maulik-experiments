"""Load the frozen proposal catalog (proposals.json). PDF parse is export-only."""

from __future__ import annotations

import json
import logging
import os
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import config

logger = logging.getLogger("proposal_loader")

_CODE_TO_NBHD = {
    "SW": "Southwest Fresno",
    "CH": "Chinatown",
    "DT": "Downtown Fresno",
}

_TYPE_RE = r"Housing|Jobs/Ec\.\s*Dev\.|Home Energy|Mobility|Greening|Multiple|Workforce"
_NUM_RE = r"[\d,]+"
_INDEX_ROW_RE = re.compile(
    rf"^(\d+)\s+({_TYPE_RE})\s*(.*?)\s+({_NUM_RE})\s+({_NUM_RE})\s+({_NUM_RE})\s*$"
)
_MONEY_RE = re.compile(r"\$?\s*([\d,]+(?:\.\d+)?)")


def _parse_dollar(text: str) -> float:
    if not text:
        return 0.0
    m = _MONEY_RE.search(text.replace("\u00a0", " "))
    if not m:
        return 0.0
    return float(m.group(1).replace(",", ""))


def _codes_to_neighborhoods(codes: List[str]) -> List[str]:
    out: List[str] = []
    for code in codes:
        name = _CODE_TO_NBHD.get(code)
        if name and name not in out:
            out.append(name)
    return out


@dataclass
class Proposal:
    id: int
    title: str
    description: str
    implementer: str
    location_text: str
    neighborhoods: List[str]
    tcc_request: float
    proposed_match: float = 0.0
    total_budget: float = 0.0
    synthetic: bool = False
    raw_text: str = field(default="", repr=False)

    @property
    def is_sw_fresno(self) -> bool:
        return "Southwest Fresno" in self.neighborhoods

    @property
    def is_chinatown(self) -> bool:
        return "Chinatown" in self.neighborhoods

    @property
    def is_downtown(self) -> bool:
        return "Downtown Fresno" in self.neighborhoods

    def neighborhood_label(self) -> str:
        return " / ".join(self.neighborhoods) if self.neighborhoods else "Unknown"

    def to_full_text(self) -> str:
        tags = []
        if self.is_sw_fresno:
            tags.append("  * SOUTHWEST FRESNO PROJECT")
        if self.is_downtown:
            tags.append("  * DOWNTOWN FRESNO PROJECT")
        sw_tag = "\n".join(tags)
        lines = [
            f"PROPOSAL #{self.id}: {self.title}",
            f"  Implementer:   {self.implementer or 'Not specified'}",
            f"  Project Area:  {self.location_text or self.neighborhood_label()}",
            f"  TCC Request:   ${self.tcc_request:,.0f}  (the only funding amount that matters)",
        ]
        if sw_tag:
            lines.append(sw_tag)
        if self.description:
            lines.append(f"  Description:   {self.description}")
        if self.synthetic:
            lines.append("  [SYNTHETIC PLACEHOLDER — not real data]")
        return "\n".join(lines)

    def to_summary(self) -> str:
        sw_tag = " *SW" if self.is_sw_fresno else ""
        dt_tag = " *DT" if self.is_downtown else ""
        return (
            f"#{self.id}: {self.title}{sw_tag}{dt_tag} "
            f"| Area: {self.neighborhood_label()} "
            f"| TCC: ${self.tcc_request:,.0f}"
            + (" [SYNTHETIC]" if self.synthetic else "")
        )


def project_index_text(proposals: List[Proposal]) -> str:
    ordered = sorted(proposals, key=lambda p: p.id)
    sw_total = sum(p.tcc_request for p in ordered if p.is_sw_fresno)
    dt_total = sum(p.tcc_request for p in ordered if p.is_downtown)
    lines = [
        "CATALOG IN ID ORDER. Copy the ID and the exact title. List position is not the ID.",
        "  #3  = H Street Development (Downtown housing). Not a complete-streets project.",
        "  #18 = H Complete Street.  #20 = Tulare Complete Streets.",
        "Each listed ID is funded at the TCC amount in this table. TCC $0 rows cannot be funded.",
        f"{'ID':>4} {'SW':^3} {'DT':^3} {'TCC':>12}  {'Area':<28}  Title",
        "-" * 100,
    ]
    for p in ordered:
        star = "*" if p.is_sw_fresno else " "
        dstar = "*" if p.is_downtown else " "
        lines.append(
            f"{p.id:>4} {star:^3} {dstar:^3} ${p.tcc_request:>11,.0f}  "
            f"{p.neighborhood_label():<28}  {p.title}"
        )
    lines += [
        "-" * 100,
        f"*SW = tagged Southwest (exclusive SW or multi-area). "
        "There is no SW dollar floor — fund on the merits.",
        f"*DT = tagged Downtown (exclusive Downtown or Downtown-tagged "
        "multi-area). There is no Downtown dollar floor.",
        f"SW / multi-area TCC subtotal (*SW): ${sw_total:,.0f}  |  "
        f"Downtown-tagged TCC subtotal (*DT): ${dt_total:,.0f}  |  "
        f"All TCC asks: ${sum(p.tcc_request for p in ordered):,.0f}  |  "
        f"Allowed budget range: ${config.MIN_BUDGET_USD:,.0f}–"
        f"${config.TOTAL_BUDGET_USD:,.0f} (anywhere in range is fine)",
    ]
    return "\n".join(lines)


def proposals_to_full_text(proposals: List[Proposal]) -> str:
    ordered = sorted(proposals, key=lambda p: p.id)
    sep = "\n" + "-" * 60 + "\n"
    return "\n".join([
        "=" * 60,
        f"FRESNO INFRASTRUCTURE PROPOSALS ({len(ordered)} total, listed by ID)",
        "=" * 60,
        "",
        project_index_text(ordered),
        "",
        "=" * 60,
        "FULL PROPOSAL DETAILS (same ID order as the catalog)",
        "=" * 60,
        "",
        sep.join(p.to_full_text() for p in ordered),
    ])


def proposals_to_summary_text(proposals: List[Proposal]) -> str:
    ordered = sorted(proposals, key=lambda p: p.id)
    lines = [
        project_index_text(ordered),
        "",
        f"COMPACT DETAIL (ID order; *SW = Southwest-tagged; "
        f"*DT = Downtown-tagged; no neighborhood floors):",
    ]
    lines += [p.to_summary() for p in ordered]
    return "\n".join(lines)


def _parse_index_page(text: str) -> Dict[int, dict]:
    lines = [l.strip() for l in (text or "").split("\n") if l.strip()]
    hits = [(i, _INDEX_ROW_RE.match(lines[i])) for i in range(len(lines))]
    hits = [(i, m) for i, m in hits if m]
    rows: Dict[int, dict] = {}
    consumed = -1
    for n, (i, m) in enumerate(hits):
        prev_i = hits[n - 1][0] if n else -1
        next_i = hits[n + 1][0] if n + 1 < len(hits) else len(lines)
        title = (m.group(3) or "").strip()
        if not title:
            start = max(prev_i + 1, consumed + 1)
            prefix = [
                lines[j] for j in range(start, i)
                if not lines[j].lower().startswith(("id type", "fresno", "concept"))
            ]
            suffix = []
            if i + 1 < next_i:
                suffix = [lines[i + 1]]
                consumed = i + 1
            title = " ".join(prefix + suffix).strip()
        pid = int(m.group(1))
        rows[pid] = {
            "title": re.sub(r"\s+", " ", title).strip(),
            "tcc": _parse_dollar(m.group(5)),
            "total": _parse_dollar(m.group(4)),
            "match": _parse_dollar(m.group(6)),
            "type": re.sub(r"\s+", " ", m.group(2)),
        }
    return rows


def _neighborhood_codes(words: list) -> List[str]:
    codes: List[str] = []
    for w in words:
        if w["text"] != "Neighborhood(s):":
            continue
        y = w["top"]
        for w2 in words:
            if w2["x0"] > 400 and abs(w2["top"] - y) < 28:
                tok = w2["text"].replace(",", "").strip()
                if tok in _CODE_TO_NBHD and tok not in codes:
                    codes.append(tok)
    return codes


def _tcc_request_from_words(words: list) -> Optional[float]:
    for w in words:
        if w["text"] != "TCC" or w["x0"] < 350:
            continue
        has_request = any(
            w2["text"] == "Request"
            and abs(w2["x0"] - w["x0"]) < 50
            and 0 <= (w2["top"] - w["top"]) < 30
            for w2 in words
        )
        if not has_request:
            continue
        for w2 in words:
            if w2["x0"] > 430 and abs(w2["top"] - w["top"]) < 22 and re.search(r"[\d$]", w2["text"]):
                return _parse_dollar(w2["text"])
    return None


def _phrase_index(joined: List[str], phrase: Tuple[str, ...], start: int = 0) -> int:
    n = len(phrase)
    for i in range(start, len(joined) - n + 1):
        if tuple(joined[i : i + n]) == phrase:
            return i
    return -1


def _left_block_between(
    words: list,
    start_phrase: Tuple[str, ...],
    end_phrases: List[Tuple[str, ...]],
    x_max: float = 380,
) -> str:
    """All left-column words after start_phrase until the earliest end phrase."""
    joined = [w["text"] for w in words]
    start_at = _phrase_index(joined, start_phrase)
    if start_at < 0:
        return ""
    start_i = start_at + len(start_phrase)
    end_i = len(words)
    for end in end_phrases:
        hit = _phrase_index(joined, end, start_i)
        if hit >= 0:
            end_i = min(end_i, hit)
    parts = [w["text"] for w in words[start_i:end_i] if w["x0"] <= x_max]
    text = re.sub(r"\s+", " ", " ".join(parts)).strip()
    if text.startswith("By the Numbers:"):
        text = text[len("By the Numbers:"):].strip()
    return text


def _parse_detail_page(page, fallback: dict) -> Proposal:
    words = page.extract_words() or []
    text = page.extract_text() or ""
    first = (text.split("\n")[0] if text else "").strip()
    pid_m = re.match(r"^(\d+)", first)
    pid = int(pid_m.group(1)) if pid_m else int(fallback.get("id") or 0)

    tcc = _tcc_request_from_words(words)
    if tcc is None:
        tcc = float(fallback.get("tcc") or 0.0)

    codes = _neighborhood_codes(words)
    neighborhoods = _codes_to_neighborhoods(codes)
    location = " / ".join(neighborhoods) if neighborhoods else "Unknown"

    implementer = _left_block_between(
        words,
        ("Proposed", "Project", "Implementer:"),
        [
            ("Project", "Location", "Identified"),
            ("Can", "Scale"),
            ("Personal", "notes:"),
        ],
    )
    description = _left_block_between(
        words,
        ("Project", "Description", "Provided", "by", "Proposer:"),
        [
            ("Proposed", "Project", "Implementer:"),
            ("Project", "Location", "Identified"),
            ("Personal", "notes:"),
        ],
    )
    title = (fallback.get("title") or "").strip() or f"Proposal {pid}"

    return Proposal(
        id=pid,
        title=title,
        description=description,
        implementer=implementer,
        location_text=location,
        neighborhoods=neighborhoods,
        tcc_request=float(tcc),
        proposed_match=float(fallback.get("match") or 0.0),
        total_budget=float(fallback.get("total") or 0.0),
        raw_text=text,
    )


def proposal_to_record(p: Proposal) -> dict:
    tcc = p.tcc_request
    return {
        "id": p.id,
        "title": p.title,
        "neighborhoods": list(p.neighborhoods),
        "tcc_request": int(tcc) if float(tcc) == int(tcc) else tcc,
        "implementer": p.implementer,
        "description": p.description,
        "synthetic": p.synthetic,
    }


def proposal_from_record(row: dict) -> Proposal:
    nbhds = list(row.get("neighborhoods") or [])
    return Proposal(
        id=int(row["id"]),
        title=str(row.get("title") or f"Proposal {row['id']}"),
        description=str(row.get("description") or ""),
        implementer=str(row.get("implementer") or ""),
        location_text=" / ".join(nbhds) if nbhds else "Unknown",
        neighborhoods=nbhds,
        tcc_request=float(row.get("tcc_request") or 0),
        synthetic=bool(row.get("synthetic")),
    )


def save_catalog(proposals: List[Proposal], path: str) -> None:
    payload = {
        "note": (
            "Frozen runtime catalog. Spot-check id / title / neighborhoods / "
            "tcc_request against the PDF before a real study run."
        ),
        "proposals": [proposal_to_record(p) for p in proposals],
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def load_catalog(path: str) -> List[Proposal]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = data["proposals"] if isinstance(data, dict) and "proposals" in data else data
    proposals = [proposal_from_record(row) for row in rows]
    proposals.sort(key=lambda p: p.id)
    return proposals


def load_proposals(
    pdf_path: Optional[str] = None,
    json_path: Optional[str] = None,
) -> List[Proposal]:
    json_path = json_path or config.PROPOSALS_JSON_PATH
    if json_path and os.path.isfile(json_path):
        logger.info("Loading frozen catalog %s", json_path)
        return load_catalog(json_path)

    proposals = load_proposals_from_pdf(pdf_path or config.PROPOSALS_PDF_PATH)
    if proposals and json_path and not any(p.synthetic for p in proposals):
        try:
            save_catalog(proposals, json_path)
            logger.info("Wrote draft catalog %s — verify against the PDF", json_path)
        except OSError as exc:
            logger.warning("Could not write catalog %s: %s", json_path, exc)
    return proposals


def load_proposals_from_pdf(pdf_path: str) -> List[Proposal]:
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed. pip install pdfplumber")
        return _synthetic_proposals()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("PDF has no pages")
            index = _parse_index_page(pdf.pages[0].extract_text() or "")
            logger.info("Page-1 index rows: %d", len(index))

            proposals: List[Proposal] = []
            for page in pdf.pages[1:]:
                text = page.extract_text() or ""
                if not text.strip():
                    continue
                first = text.split("\n")[0]
                pid_m = re.match(r"^(\d+)", first.strip())
                pid = int(pid_m.group(1)) if pid_m else len(proposals) + 1
                fb = dict(index.get(pid) or {})
                fb["id"] = pid
                proposals.append(_parse_detail_page(page, fb))

        if not proposals:
            raise ValueError("No proposals extracted")

        proposals.sort(key=lambda p: p.id)
        sw_count = sum(1 for p in proposals if p.is_sw_fresno)
        sw_tcc = sum(p.tcc_request for p in proposals if p.is_sw_fresno)
        logger.info(
            "Loaded %d proposals; %d SW Fresno; SW TCC total $%s",
            len(proposals), sw_count, f"{sw_tcc:,.0f}",
        )
        return proposals

    except FileNotFoundError:
        logger.error("PDF not found at %s", pdf_path)
    except Exception as exc:
        logger.error("Failed to parse PDF at %s: %s", pdf_path, exc)

    return _synthetic_proposals()


def _synthetic_proposals() -> List[Proposal]:
    rng = random.Random(config.RANDOM_SEED)
    types = [
        "Pedestrian Safety Improvements", "Stormwater Management Facility",
        "Community Garden", "Streetscape Revitalization", "Safe Routes to School",
        "Affordable Housing Rehab", "Tree Planting", "Transit Stop Upgrades",
    ]
    nbhd_pool = (
        [("Southwest Fresno",)] * 14
        + [("Chinatown",)] * 9
        + [("Downtown Fresno",)] * 9
        + [("Southwest Fresno", "Chinatown")] * 3
        + [("Southwest Fresno", "Downtown Fresno")] * 2
    )
    rng.shuffle(nbhd_pool)
    costs = [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000, 3_000_000]
    proposals: List[Proposal] = []
    for i in range(1, 38):
        nbhds = list(rng.choice(nbhd_pool))
        tcc = float(rng.choice(costs))
        proposals.append(Proposal(
            id=i,
            title=f"[SYNTHETIC] {rng.choice(types)} — {' / '.join(nbhds)}",
            description=f"Synthetic placeholder proposal #{i}.",
            implementer="Synthetic Implementer",
            location_text=" / ".join(nbhds),
            neighborhoods=nbhds,
            tcc_request=tcc,
            synthetic=True,
            raw_text=f"[SYNTHETIC PROPOSAL #{i}]",
        ))
    logger.warning("Using synthetic proposals. Do not report as real findings.")
    return proposals
