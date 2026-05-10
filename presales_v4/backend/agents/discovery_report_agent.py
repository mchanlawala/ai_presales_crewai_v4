"""
agents/discovery_report_agent.py
----------------------------------
Corrected BRD with proper NFR and stakeholder tables.
"""
import datetime, os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_LIGHT, BRAND_MID,
    get_styles, default_table_style, strip_markdown, nl2br,
)


class DiscoveryReportAgent:
    def __init__(self):
        self.s = get_styles()

    def _fmt_req(self, req_obj) -> str:
        if isinstance(req_obj, str): return req_obj
        if isinstance(req_obj, dict):
            title = req_obj.get("requirement","") or req_obj.get("title","")
            details = req_obj.get("details",[])
            if isinstance(details, list) and details:
                return f"{title} ({'; '.join(details)})"
            return title
        return str(req_obj)

    def run(self, state: dict, output_path: str = "output/discovery_report.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        req = state.get("requirements", {})
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []

        # Banner
        banner = Table([[Paragraph("Business Requirements Document", s["cover_title"])]],
                       colWidths=[6.8*inch])
        banner.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
                                    ("TOPPADDING",(0,0),(-1,-1),20),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),20),
                                    ("LEFTPADDING",(0,0),(-1,-1),18)]))
        st.append(banner); st.append(Spacer(1,6))
        industry = req.get("industry","Manufacturing")
        today = datetime.date.today().strftime("%d %B %Y")
        st.append(Paragraph(f"{industry} | MES Pre-Sales Discovery | {today}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT))
        st.append(Spacer(1,12))

        # 1. Executive Summary
        st.append(Paragraph("1. Executive Summary", s["section_heading"]))
        st.append(Paragraph(
            f"MES implementation for a <b>{industry}</b> manufacturer producing <b>{req.get('product','N/A')}</b> "
            f"at <b>{req.get('production_capacity','N/A')}</b>. Current systems: "
            f"{', '.join(req.get('current_systems',[])) or 'None listed'}.", s["body"]))
        st.append(Spacer(1,10))

        # 2. Business Objectives
        st.append(Paragraph("2. Business Objectives & Pain Points", s["section_heading"]))
        pp = req.get("pain_points", [])
        if pp:
            for p in pp: st.append(Paragraph(f"• {p}", s["body"]))
        else:
            st.append(Paragraph("No specific pain points captured.", s["body"]))
        st.append(Spacer(1,10))

        # 3. Functional Requirements
        st.append(Paragraph("3. Functional Requirements", s["section_heading"]))
        reqs = req.get("requirements", [])
        if reqs:
            rows = [[Paragraph("#", s["table_header"]),
                     Paragraph("Requirement", s["table_header"])]]
            for i, r in enumerate(reqs, 1):
                rows.append([Paragraph(str(i), s["table_cell"]),
                             Paragraph(self._fmt_req(r), s["table_cell"])])
            tbl = Table(rows, colWidths=[0.4*inch, 6.1*inch])
            tbl.setStyle(default_table_style())
            st.append(tbl)
        else:
            st.append(Paragraph("To be elaborated in workshops.", s["body"]))
        st.append(Spacer(1,10))

        # 4. Non-Functional Requirements (FIXED HEADER)
        st.append(Paragraph("4. Non-Functional Requirements", s["section_heading"]))
        nfr_data = [
            ["Category", "Requirement"],
            ["Availability", "99.5% uptime during production shifts"],
            ["Performance", "Real‑time data refresh ≤ 5 seconds"],
            ["Security", "Role‑based access control; audit logs retained 3 years"],
            ["Scalability", "Architecture must support 2× production line growth"],
            ["Disaster Rec.", "RTO ≤ 4 hours; RPO ≤ 1 hour"],
            ["Integration", f"ERP: {req.get('erp','N/A')} via REST/IDoc; OPC UA for machines"],
        ]
        nfr_tbl = Table(
            [[Paragraph(c[0], s["table_header"]), Paragraph(c[1], s["table_cell"])] for c in nfr_data],
            colWidths=[1.6*inch, 5.0*inch]
        )
        nfr_tbl.setStyle(default_table_style())
        st.append(nfr_tbl)
        st.append(Spacer(1,10))

        # 5. Success Criteria
        st.append(Paragraph("5. Success Criteria", s["section_heading"]))
        for c in [
            "Production tracking accuracy ±2%",
            "Full batch genealogy from wafer to module",
            "Real‑time quality alerts ≤ 10 seconds",
            "ERP–MES synchronisation latency ≤ 30 seconds",
            "OEE dashboard available within 1 hour of go‑live",
        ]:
            st.append(Paragraph(f"✓ {c}", s["body"]))
        st.append(Spacer(1,10))

        # 6. Stakeholders (FIXED TABLE)
        st.append(Paragraph("6. Key Stakeholders", s["section_heading"]))
        sh = [
            ["Role", "Responsibility", "Involvement"],
            ["Plant Manager", "Executive sponsor", "Sign‑off"],
            ["IT Manager", "Infrastructure & security", "Architecture review"],
            ["Production Supv.", "Shop‑floor champion", "UAT lead"],
            ["Quality Manager", "QMS requirements", "Requirements & UAT"],
            ["SAP Team", "ERP integration point", "Integration testing"],
        ]
        sh_tbl = Table(
            [[Paragraph(r[0], s["table_header"]),
              Paragraph(r[1], s["table_cell"]),
              Paragraph(r[2], s["table_cell"])] for r in sh],
            colWidths=[1.7*inch, 3.0*inch, 1.8*inch]
        )
        sh_tbl.setStyle(default_table_style())
        st.append(sh_tbl)
        st.append(Spacer(1,10))

        # 7. Assumptions & Constraints
        st.append(Paragraph("7. Assumptions & Constraints", s["section_heading"]))
        for a in [
            "Customer will provide network access to all production machines.",
            "SAP system landscape is stable and not under major upgrade during implementation.",
            "At least one super‑user per production line nominated before Phase 2.",
            "Hardware procurement (servers, HMIs, scanners) is the customer's responsibility.",
        ]:
            st.append(Paragraph(f"• {a}", s["body"]))

        doc.build(st)
        state["discovery_report_path"] = output_path
        return state