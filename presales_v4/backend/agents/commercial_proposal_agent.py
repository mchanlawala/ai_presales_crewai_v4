"""
agents/commercial_proposal_agent.py
------------------------------------
Document 11 of 12: Commercial Proposal
Enhanced with service breakdown, detailed payment milestones, full team, and terms.
"""
import datetime, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from pdf_styles import BRAND_ACCENT, BRAND_DARK, BRAND_MID, get_styles, default_table_style

class CommercialProposalAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/commercial_proposal.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        req = state.get("requirements", {})
        est = state.get("estimation", {})
        self._build_pdf(req, est, output_path)
        state["commercial_proposal_path"] = output_path
        return state

    def _build_pdf(self, req: dict, est: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []

        banner = Table([[Paragraph(
            "Commercial Proposal<br/><font size=14>MES / APS / WMS Implementation Services</font>",
            s["cover_title"]
        )]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
            ("TOPPADDING",(0,0),(-1,-1),22),
            ("BOTTOMPADDING",(0,0),(-1,-1),22),
            ("LEFTPADDING",(0,0),(-1,-1),18)
        ]))
        st.append(banner); st.append(Spacer(1,6))
        st.append(Paragraph(
            f"Prepared for: {req.get('industry','Solar')} Manufacturer | "
            f"{datetime.date.today().strftime('%d %B %Y')}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT))
        st.append(Spacer(1,14))

        # ── Key numbers ───────────────────────────────────────────────────
        total_cost   = est.get("estimated_cost_usd", 0)
        total_effort = est.get("total_effort_person_months", 0)
        total_months = est.get("total_duration_months", 0)
        hw_estimate  = 115000  # hardware not in service cost
        amc_annual   = max(25000, int(total_cost * 0.03))

        # ── 1. Investment Summary ─────────────────────────────────────────
        st.append(Paragraph("1. Investment Summary", s["section_heading"]))
        summary = [
            ["Category", "Cost (USD)", "Notes"],
            ["Implementation Services (Fixed Price)",
             f"${total_cost:,.0f}",
             f"{total_effort} person-months over {total_months} months"],
            ["Hardware & Infrastructure (customer scope)",
             f"~${hw_estimate:,.0f}",
             "Servers, edge gateways, OEE screens — procured by customer per HLD spec"],
            ["Year 1 Software License",
             "Included",
             "Bundled with implementation for Year 1"],
            ["Annual Maintenance & Support (AMC, Yr 2+)",
             f"${amc_annual:,.0f}/year",
             "Helpdesk, bug fixes, minor enhancements, quarterly health check"],
            ["TOTAL YEAR 1 INVESTMENT",
             f"${total_cost + hw_estimate:,.0f}",
             "Services + hardware (indicative)"],
        ]
        self._tbl(st, summary, s, [2.6*inch, 1.6*inch, 2.4*inch])
        st.append(Spacer(1,12))

        # ── 2. Service Component Breakdown ────────────────────────────────
        st.append(Paragraph("2. Service Component Breakdown", s["section_heading"]))
        components = [
            ["Service Component", "Effort (PM)", "Cost (USD)", "Deliverable"],
            ["Project Management & Governance", "10%",
             f"${int(total_cost*0.10):,.0f}", "Project charter, weekly reports, risk register, change log"],
            ["Discovery & Blueprint (Phase 1)", "15%",
             f"${int(total_cost*0.15):,.0f}", "FSD, AS-IS/TO-BE maps, integration design spec"],
            ["Core MES Configuration (Phase 2)", "25%",
             f"${int(total_cost*0.25):,.0f}", "Configured MES, SAP integration, QMS, OEE dashboards"],
            ["Equipment Integration (Phase 3)", "25%",
             f"${int(total_cost*0.25):,.0f}", "OPC UA/Kafka per machine; PDI/PDO agent; AI EL classifier"],
            ["PODISE / APS Deployment (Phase 4)", "15%",
             f"${int(total_cost*0.15):,.0f}", "Scheduling engine, Gantt portal, SAP order dressing"],
            ["Testing, Go-Live & Training (Phase 5)", "10%",
             f"${int(total_cost*0.10):,.0f}", "UAT, load test, DR test, operator training, go-live support"],
            ["TOTAL", f"{total_effort} PM",
             f"${total_cost:,.0f}", ""],
        ]
        self._tbl(st, components, s, [2.1*inch, 0.8*inch, 1.2*inch, 2.5*inch])
        st.append(Spacer(1,12))

        # ── 3. Payment Schedule ────────────────────────────────────────────
        st.append(Paragraph("3. Payment Schedule", s["section_heading"]))
        schedule = [
            ["Milestone", "% of Services", "Amount (USD)", "Expected Timing"],
            ["Contract signing", "20%", f"${int(total_cost*0.20):,.0f}", "Week 1"],
            ["Phase 1 completion (FSD sign-off)", "15%", f"${int(total_cost*0.15):,.0f}", "Week 12"],
            ["Phase 2 completion (MES UAT pass)", "25%", f"${int(total_cost*0.25):,.0f}", "Week 28"],
            ["Phase 3 completion (machine integration validated)", "20%", f"${int(total_cost*0.20):,.0f}", "Week 32"],
            ["Pilot line go-live acceptance", "15%", f"${int(total_cost*0.15):,.0f}", "Week 36"],
            ["All lines live + project closure", "5%", f"${int(total_cost*0.05):,.0f}", "Week 52"],
            ["TOTAL", "100%", f"${total_cost:,.0f}", ""],
        ]
        self._tbl(st, schedule, s, [2.4*inch, 1.0*inch, 1.2*inch, 1.9*inch])
        st.append(Spacer(1,12))

        # ── 4. Proposed Team ──────────────────────────────────────────────
        st.append(Paragraph("4. Proposed Team Structure", s["section_heading"]))
        team = [
            ["Role", "Responsibility", "Phase", "Allocation"],
            ["Program Manager", "Project governance, client communication, risk management", "All phases", "Full-time"],
            ["Solution Architect", "System design, integration oversight, technical decisions", "Phase 1–4", "Full-time"],
            ["Solar MES Consultant", "Manufacturing process mapping, MES configuration, QMS", "Phase 1–3", "Full-time"],
            ["APS / PODISE Expert", "Scheduling logic, lot-split rules, SAP order dressing", "Phase 4", "Full-time"],
            ["SAP Integration Engineer", "IDoc, BAPI, REST connectors; SAP test", "Phase 2–3", "Part-time"],
            ["OPC UA / Kafka Engineer", "Machine connectivity, edge deployment, Kafka topics", "Phase 3", "Full-time"],
            ["AI / Data Scientist", "EL image classifier, Ollama deployment, PDI/PDO analytics", "Phase 3–4", "Part-time"],
            ["QA Lead", "Test planning, UAT coordination, defect management", "Phase 5", "Full-time"],
            ["Change Management", "Training, super-user programme, adoption support", "Phase 5–6", "Part-time"],
        ]
        self._tbl(st, team, s, [1.5*inch, 2.5*inch, 1.0*inch, 0.9*inch])
        st.append(Spacer(1,12))

        # ── 5. Commercial Terms ────────────────────────────────────────────
        st.append(Paragraph("5. Commercial Terms & Assumptions", s["section_heading"]))
        terms = [
            ("Pricing basis", "Fixed price per agreed scope; change requests priced separately via Change Order process"),
            ("Currency", "All prices in USD; INR pricing available on request"),
            ("Travel & Living", "Included in the fixed price for on-site team; up to 3 days/week on-site"),
            ("Change requests", "Scope changes priced within 5 business days; requires written approval before work starts"),
            ("Warranty period", "3-month defect warranty post go-live; defects in agreed scope fixed at no charge"),
            ("Intellectual property", "Custom code developed for this project: customer owns it post final payment"),
            ("Confidentiality", "Mutual NDA applies; customer data is never shared outside project team"),
            ("Validity", "This commercial proposal is valid for 60 days from the date above"),
        ]
        for term, detail in terms:
            st.append(Paragraph(f"<b>{term}:</b> {detail}", s["body"]))
        st.append(Spacer(1,12))

        # ── 6. Next Steps ─────────────────────────────────────────────────
        st.append(Paragraph("6. Next Steps to Proceed", s["section_heading"]))
        steps = [
            "Customer reviews commercial terms and raises any questions within 5 business days.",
            "Technical deep-dive workshop scheduled (2 hours): IT, Production, Quality, SAP teams.",
            "Commercial agreement and NDA signed.",
            "Project kick-off within 2 weeks of contract signature.",
            "Phase 0 (Pre-Project Assessment) commences: machine connectivity audit + SAP landscape.",
        ]
        for i, step in enumerate(steps, 1):
            st.append(Paragraph(f"{i}. {step}", s["body"]))

        doc.build(st)

    def _tbl(self, story, data, s, widths):
        rows = [[Paragraph(str(c), s["table_header"] if i==0 else s["table_cell"])
                 for c in row] for i, row in enumerate(data)]
        tbl = Table(rows, colWidths=widths)
        tbl.setStyle(default_table_style())
        story.append(tbl)