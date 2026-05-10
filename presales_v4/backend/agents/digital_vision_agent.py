"""
agents/digital_vision_agent.py
-------------------------------
Generates a one‑page Digital Transformation Vision document.
Result → state["digital_vision_path"]
"""
import datetime, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID,
    get_styles, default_table_style
)

class DigitalVisionAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/digital_vision.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        req = state.get("requirements", {})
        self._build_pdf(req, output_path)
        state["digital_vision_path"] = output_path
        return state

    def _build_pdf(self, req: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []

        banner = Table([[Paragraph("Digital Transformation Vision<br/><font size=14>MES & AI‑Native Manufacturing</font>", s["cover_title"])]],
                       colWidths=[6.8*inch])
        banner.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
                                    ("TOPPADDING",(0,0),(-1,-1),22),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),22),
                                    ("LEFTPADDING",(0,0),(-1,-1),18)]))
        st.append(banner); st.append(Spacer(1,6))
        st.append(Paragraph(f"Prepared for: {req.get('industry','Solar')} Manufacturer | {datetime.date.today().strftime('%d %B %Y')}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT)); st.append(Spacer(1,14))

        st.append(Paragraph("Vision Statement", s["section_heading"]))
        st.append(Paragraph(
            f"To become a data‑driven, AI‑native solar manufacturer where every cell, module, and pallet is tracked in real time, "
            f"quality is predicted before it fails, and the factory optimises itself autonomously. "
            f"This transformation will turn {req.get('production_capacity','N/A')} of production into a fully visible, "
            f"ALMM‑compliant, and highly efficient digital operation.",
            s["body"])); st.append(Spacer(1,12))

        st.append(Paragraph("Business Drivers", s["section_heading"]))
        drivers = [
            "Real‑time visibility into production OEE and quality (FPY)",
            "Complete material genealogy for ALMM compliance and warranty reduction",
            "Intelligent scheduling (PODISE) to maximise line utilisation and on‑time delivery",
            "Predictive maintenance to cut unplanned downtime by >25%",
            "AI‑powered quality inspection to reduce manual checks and warranty claims",
        ]
        for d in drivers: st.append(Paragraph(f"• {d}", s["body"]))
        st.append(Spacer(1,12))

        st.append(Paragraph("Expected Benefits", s["section_heading"]))
        benefits = [
            ["Benefit", "Impact"],
            ["OEE Improvement", "+8‑12%"],
            ["First Pass Yield", ">98%"],
            ["Scrap Reduction", "30‑40%"],
            ["Warranty Claims Reduction", "20‑30%"],
            ["Audit Preparation Time", "80% reduction"],
            ["Operator Efficiency", "50%+ reduction in manual data entry"],
        ]
        ben_tbl = Table([[Paragraph(c[0], s["table_header"]), Paragraph(c[1], s["table_cell"])] for c in benefits],
                        colWidths=[3.0*inch, 3.5*inch])
        ben_tbl.setStyle(default_table_style()); st.append(ben_tbl)

        doc.build(st)