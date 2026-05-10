"""
agents/poc_plan_agent.py
-------------------------
Generates a Proof‑of‑Concept (PoC) Plan PDF.
Result → state["poc_plan_path"]
"""
import datetime, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID,
    get_styles, default_table_style,
)

class PoCPlanAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/poc_plan.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        req = state.get("requirements", {})
        self._build_pdf(req, output_path)
        state["poc_plan_path"] = output_path
        return state

    def _build_pdf(self, req: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []

        banner = Table([[Paragraph("Proof of Concept (PoC) Plan<br/><font size=14>MES / APS Pilot</font>", s["cover_title"])]],
                       colWidths=[6.8*inch])
        banner.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
                                    ("TOPPADDING",(0,0),(-1,-1),22),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),22),
                                    ("LEFTPADDING",(0,0),(-1,-1),18)]))
        st.append(banner); st.append(Spacer(1,6))
        st.append(Paragraph(f"Prepared for: {req.get('industry','Solar')} Manufacturer | {datetime.date.today().strftime('%d %B %Y')}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT)); st.append(Spacer(1,14))

        st.append(Paragraph("1. PoC Objective", s["section_heading"]))
        st.append(Paragraph(
            "Validate the MES/APS solution on a pilot production line to demonstrate real‑time production tracking, "
            "quality traceability, OEE dashboards, and PODISE scheduling within a 4‑week period. "
            "Success will be measured against predefined KPIs.",
            s["body"])); st.append(Spacer(1,12))

        st.append(Paragraph("2. Scope", s["section_heading"]))
        scope = [
            "Pilot Line: 1 production line (e.g., Line 1)",
            "Machines: 2‑3 critical machines (stringer, laminator, flash tester)",
            "Integration: OPC UA data capture, manual PDI/PDO entry for other stations",
            "MES Modules: SFDC, Production Tracking, OEE Dashboard, Quality Management, PODISE scheduling",
            "Exclusions: WMS, full ERP integration (simulated with sample data)",
        ]
        for item in scope: st.append(Paragraph(f"• {item}", s["body"]))
        st.append(Spacer(1,12))

        st.append(Paragraph("3. PoC Timeline", s["section_heading"]))
        timeline = [
            ["Week", "Activities", "Deliverables"],
            ["1", "Setup OPC UA connectivity, install MES core, configure machines", "Connected machines, live data feed"],
            ["2", "Configure OEE dashboards, quality checkpoints, PDI/PDO workflows", "OEE dashboards live, quality data capture"],
            ["3", "Deploy PODISE, create sample orders, run scheduling scenarios", "Schedule Gantt, order traceability"],
            ["4", "User training, UAT, KPI measurement, feedback session", "UAT sign‑off, PoC report"],
        ]
        t_tbl = Table([[Paragraph(c, s["table_header"]) for c in timeline[0]]] +
                      [[Paragraph(c, s["table_cell"]) for c in row] for row in timeline[1:]],
                      colWidths=[0.6*inch, 3.0*inch, 2.9*inch])
        t_tbl.setStyle(default_table_style()); st.append(t_tbl)
        st.append(Spacer(1,12))

        st.append(Paragraph("4. Success Metrics", s["section_heading"]))
        metrics = [
            ["Metric", "Target"],
            ["OEE visibility (real‑time)", "OEE calculated and displayed within 10 sec of machine event"],
            ["Production tracking accuracy", ">95% of actual output recorded automatically"],
            ["Quality traceability", "Every module serial linked to flash test & EL results"],
            ["PODISE scheduling response", "Sales order → production order in <5 seconds"],
            ["User acceptance", "80% of operators rate system as easy to use"],
        ]
        m_tbl = Table([[Paragraph(c[0], s["table_header"]), Paragraph(c[1], s["table_cell"])] for c in metrics],
                      colWidths=[2.5*inch, 4.0*inch])
        m_tbl.setStyle(default_table_style()); st.append(m_tbl)
        st.append(Spacer(1,12))

        st.append(Paragraph("5. Customer Responsibilities", s["section_heading"]))
        cust = [
            "Provide access to pilot line and machines (including network connectivity)",
            "Nominate 2 super‑users for UAT and training",
            "Provide sample sales orders and master data (BOM, routings)",
            "Assign IT resource for firewall/network configuration",
        ]
        for c in cust: st.append(Paragraph(f"• {c}", s["body"]))
        st.append(Spacer(1,12))

        st.append(Paragraph("6. PoC Deliverables", s["section_heading"]))
        deliv = [
            "Live MES instance on pilot line with real‑time dashboards",
            "PoC evaluation report including KPI results and lessons learned",
            "Recommendation for full‑scale implementation (updated proposal)",
            "Training session for operators and supervisors",
        ]
        for d in deliv: st.append(Paragraph(f"• {d}", s["body"]))

        doc.build(st)