"""Generate one-page proposal PDFs so the ingest pipeline can be tested without uploads."""

from __future__ import annotations

from pathlib import Path

from .sample_data import load_sample_proposals


def generate_sample_pdfs(out_dir: str | Path, combined: bool = False) -> list[Path]:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    proposals = load_sample_proposals()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "T",
        parent=styles["Heading1"],
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, leading=14, spaceBefore=6)
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9.5, leading=12.5)

    def story_for(p):
        return [
            Paragraph("City of Fresno — Environmental Infrastructure Bond ($70M)", styles["Italic"]),
            Spacer(1, 0.08 * inch),
            Paragraph(f"{p.id}: {p.title}", title_style),
            Paragraph(f"<b>ID:</b> {p.id}", body),
            Paragraph(
                f"<b>Cost:</b> ${p.cost_usd:,.0f} &nbsp;|&nbsp; "
                f"<b>Neighborhood:</b> {p.neighborhood} &nbsp;|&nbsp; "
                f"<b>Category:</b> {p.category}",
                body,
            ),
            Paragraph("<b>What it is</b>", h2),
            Paragraph(p.description, body),
            Paragraph("<b>Who it helps</b>", h2),
            Paragraph(p.who_it_helps or p.beneficiaries, body),
            Paragraph("<b>Scalability</b>", h2),
            Paragraph(p.scalability or "—", body),
            Paragraph("<b>Timeline</b>", h2),
            Paragraph(p.timeline or "—", body),
            Paragraph("<b>Co-benefits</b>", h2),
            Paragraph(p.cobenefits or "—", body),
            Paragraph("<b>Maintenance</b>", h2),
            Paragraph(p.maintenance or "—", body),
        ]

    paths: list[Path] = []
    if combined:
        dest = out_dir / "all_proposals.pdf"
        doc = SimpleDocTemplate(
            str(dest),
            pagesize=letter,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )
        story = []
        for i, p in enumerate(proposals):
            story.extend(story_for(p))
            if i != len(proposals) - 1:
                story.append(PageBreak())
        doc.build(story)
        paths.append(dest)
        return paths

    for p in proposals:
        dest = out_dir / f"{p.id}_{_slug(p.title)}.pdf"
        doc = SimpleDocTemplate(
            str(dest),
            pagesize=letter,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )
        doc.build(story_for(p))
        paths.append(dest)
    return paths


def _slug(title: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in " -" else "" for ch in title)
    return "_".join(keep.lower().split())[:40]
