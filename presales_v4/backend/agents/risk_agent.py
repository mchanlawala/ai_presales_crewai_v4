"""
agents/risk_agent.py
---------------------
Generates a risk assessment PDF using LLM-identified project risks.
Result → state["risk_assessment_path"]
"""
import datetime
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table
)
from langchain_core.messages import HumanMessage

from json_utils import parse_json
from llm_factory import get_llm
from pdf_styles import get_styles, default_table_style, BRAND_DARK, BRAND_MID, BRAND_ACCENT


# ── Fallback risks used when LLM fails ───────────────────────────────────────
_DEFAULT_RISKS = [
    {
        "risk": "ERP integration complexity",
        "probability": "Medium",
        "impact": "Schedule delay of 4-6 weeks",
        "mitigation": "Use pre-built SAP connector; allocate dedicated integration sprint",
    },
    {
        "risk": "Machine data unavailability",
        "probability": "High",
        "impact": "Incomplete OEE tracking",
        "mitigation": "Perform connectivity audit in Phase 1; add OPC UA retrofits where needed",
    },
    {
        "risk": "End-user adoption resistance",
        "probability": "Medium",
        "impact": "Reduced ROI realisation",
        "mitigation": "Structured change management, super-user network, on-floor training",
    },
    {
        "risk": "Data quality issues in legacy systems",
        "probability": "High",
        "impact": "Incorrect production reports",
        "mitigation": "Data cleansing sprint in Phase 1; master data governance policy",
    },
    {
        "risk": "Scope creep from custom development",
        "probability": "Medium",
        "impact": "15-25% cost overrun",
        "mitigation": "Fixed-scope contract for Phase 1; change request process enforced",
    },
]

_PROB_COLOR = {
    "High":   colors.HexColor("#FDECEA"),
    "Medium": colors.HexColor("#FFF3CD"),
    "Low":    colors.HexColor("#D4EDDA"),
}


class RiskAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.styles = get_styles()

    def run(self, state: dict, output_path: str = "output/risk_assessment.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        risks = self._generate_risks(state)
        self._build_pdf(risks, output_path, state)
        state["risk_assessment_path"] = output_path
        return state

    # ── Risk generation ────────────────────────────────────────────────────────

    def _generate_risks(self, state: dict) -> list:
        req_json = json.dumps(state.get("requirements", {}))
        prompt = f"""
You are a manufacturing project risk manager.
Based on the project requirements below, identify the top 6 project risks.

For each risk return a JSON object with exactly these keys:
  "risk"        – concise risk title (max 8 words)
  "probability" – one of: High | Medium | Low
  "impact"      – one sentence describing the consequence
  "mitigation"  – one concrete mitigation action

Return ONLY a JSON array of 6 objects. No explanation.

Requirements: {req_json}
"""
        try:
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            risks = parse_json(resp.content, fallback=[])
            if isinstance(risks, list) and len(risks) >= 3:
                return risks
        except Exception as exc:
            print(f"   ⚠️  RiskAgent LLM failed: {exc}")
        return _DEFAULT_RISKS

    # ── PDF generation ─────────────────────────────────────────────────────────

    def _build_pdf(self, risks: list, path: str, state: dict):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40,
        )
        s = self.styles
        story = []

        # ── Header ────────────────────────────────────────────────────────────
        story.append(Paragraph("Risk Assessment Report", s["section_heading"]))
        req = state.get("requirements", {})
        story.append(Paragraph(
            f"Project: MES Implementation – {req.get('industry','Manufacturing')} | "
            f"Date: {datetime.date.today().strftime('%d %B %Y')}",
            s["body"],
        ))
        story.append(Spacer(1, 14))

        # ── Risk legend ───────────────────────────────────────────────────────
        legend_data = [
            [Paragraph("Probability Legend", s["table_header"]),
             Paragraph("Colour", s["table_header"])],
            [Paragraph("High",   s["table_cell"]), ""],
            [Paragraph("Medium", s["table_cell"]), ""],
            [Paragraph("Low",    s["table_cell"]), ""],
        ]
        legend = Table(legend_data, colWidths=[1.5*inch, 0.8*inch])
        legend.setStyle(default_table_style())
        legend.setStyle([
            ("BACKGROUND", (0, 1), (-1, 1), _PROB_COLOR["High"]),
            ("BACKGROUND", (0, 2), (-1, 2), _PROB_COLOR["Medium"]),
            ("BACKGROUND", (0, 3), (-1, 3), _PROB_COLOR["Low"]),
        ])
        story.append(legend)
        story.append(Spacer(1, 14))

        # ── Risk table ────────────────────────────────────────────────────────
        header = [
            Paragraph("Risk", s["table_header"]),
            Paragraph("Probability", s["table_header"]),
            Paragraph("Impact", s["table_header"]),
            Paragraph("Mitigation", s["table_header"]),
        ]
        rows = [header]
        for i, r in enumerate(risks):
            prob = r.get("probability", "Medium")
            row = [
                Paragraph(r.get("risk", ""), s["table_cell"]),
                Paragraph(prob, s["table_cell"]),
                Paragraph(r.get("impact", ""), s["table_cell"]),
                Paragraph(r.get("mitigation", ""), s["table_cell"]),
            ]
            rows.append(row)

        tbl = Table(rows, colWidths=[1.6*inch, 0.9*inch, 2.0*inch, 2.2*inch])
        style = default_table_style()

        # Colour-code probability rows
        for i, r in enumerate(risks, start=1):
            bg = _PROB_COLOR.get(r.get("probability", "Medium"), colors.white)
            style.add("BACKGROUND", (1, i), (1, i), bg)

        tbl.setStyle(style)
        story.append(tbl)

        # ── Summary ───────────────────────────────────────────────────────────
        story.append(Spacer(1, 16))
        high_count   = sum(1 for r in risks if r.get("probability") == "High")
        medium_count = sum(1 for r in risks if r.get("probability") == "Medium")
        story.append(Paragraph(
            f"Summary: {high_count} High-probability risks and {medium_count} Medium-probability risks "
            f"identified. All mitigation actions should be tracked in the project risk register.",
            s["body"],
        ))

        doc.build(story)
