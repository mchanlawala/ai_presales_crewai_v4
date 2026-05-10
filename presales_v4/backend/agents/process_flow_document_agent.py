"""
agents/process_flow_document_agent.py
--------------------------------------
Generates a Process Flow PDF containing AS‑IS and TO‑BE diagrams with explanatory text.
Result → state["process_flow_document_path"]
"""
import datetime, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID,
    get_styles, default_table_style,
)

class ProcessFlowDocumentAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/process_flow.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._build_pdf(state, output_path)
        state["process_flow_document_path"] = output_path
        return state

    def _build_pdf(self, state: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []
        req = state.get("requirements", {})

        banner = Table([[Paragraph("Process Flow Documentation<br/><font size=14>AS‑IS / TO‑BE Analysis</font>", s["cover_title"])]],
                       colWidths=[6.8*inch])
        banner.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
                                    ("TOPPADDING",(0,0),(-1,-1),22),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),22),
                                    ("LEFTPADDING",(0,0),(-1,-1),18)]))
        st.append(banner); st.append(Spacer(1,6))
        st.append(Paragraph(f"Prepared for: {req.get('industry','Solar')} Manufacturer | {datetime.date.today().strftime('%d %B %Y')}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT)); st.append(Spacer(1,14))

        # AS‑IS
        st.append(Paragraph("1. AS‑IS Process (Current State)", s["section_heading"]))
        st.append(Paragraph("Manual, paper‑based tracking with spreadsheets. Operators record counts manually; quality tests are logged in notebooks or Excel. No real‑time visibility, OEE is calculated after shift end, and traceability is batch‑level at best.", s["body"]))
        st.append(Spacer(1,8))
        asis_path = state.get("asis_diagram_path")
        if asis_path and os.path.exists(asis_path):
            st.append(Image(os.path.abspath(asis_path), width=4.5*inch, height=3.0*inch))
        else:
            st.append(Paragraph("AS‑IS diagram not available.", s["small"]))
        st.append(Spacer(1,16))

        # TO‑BE
        st.append(Paragraph("2. TO‑BE Process (Future State with MES)", s["section_heading"]))
        st.append(Paragraph("Fully digital, AI‑native. Sales orders flow into PODISE for real‑time scheduling. Every machine data is captured via OPC UA and streamed through Kafka to the MES. Quality inspection is AI‑powered (AOI/EL), and full genealogy is maintained. Dispatch is optimised with system‑directed loading and ALMM COC auto‑generation.", s["body"]))
        st.append(Spacer(1,8))
        tobe_path = state.get("tobe_diagram_path")
        if tobe_path and os.path.exists(tobe_path):
            st.append(Image(os.path.abspath(tobe_path), width=4.5*inch, height=3.0*inch))
        else:
            st.append(Paragraph("TO‑BE diagram not available.", s["small"]))
        st.append(Spacer(1,16))

        # Summary table
        st.append(Paragraph("3. Key Differences", s["section_heading"]))
        diff = [
            ["Aspect", "AS‑IS", "TO‑BE"],
            ["Production tracking", "Manual Excel/logs", "Real‑time SFDC + OEE dashboards"],
            ["Quality", "Paper forms, manual EL", "AI‑AOI/EL classification, flash test auto‑capture"],
            ["Scheduling", "Planner’s spreadsheet", "PODISE real‑time APS with Gantt"],
            ["Traceability", "Batch level (no serial)", "Full genealogy wafer→module; serial‑level ALMM"],
            ["Dispatch", "Manual loading, paper COC", "System‑directed loading, digital COC"],
        ]
        diff_tbl = Table([[Paragraph(c, s["table_header"]) for c in diff[0]]] +
                         [[Paragraph(c, s["table_cell"]) for c in row] for row in diff[1:]],
                         colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
        diff_tbl.setStyle(default_table_style()); st.append(diff_tbl)

        doc.build(st)