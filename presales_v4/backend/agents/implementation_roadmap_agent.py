"""
agents/implementation_roadmap_agent.py
----------------------------------------
Document 9 of 12: Implementation Roadmap
A dedicated, detailed roadmap document covering all 7 phases with
Gantt-style timeline, milestones, RACI, go/no-go criteria.
Result → state["roadmap_pdf_path"]
"""
import datetime, os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID, BRAND_LIGHT,
    get_styles, default_table_style,
)


_PHASE_COLORS = {
    "Phase 0": colors.HexColor("#EAF2FB"),  # light blue
    "Phase 1": colors.HexColor("#D4EDDA"),  # light green
    "Phase 2": colors.HexColor("#FFF3CD"),  # light amber
    "Phase 3": colors.HexColor("#FDECEA"),  # light red
    "Phase 4": colors.HexColor("#E8D5F5"),  # light purple
    "Phase 5": colors.HexColor("#D4EDDA"),  # light green
    "Phase 6": colors.HexColor("#EAF2FB"),  # light blue
}


class ImplementationRoadmapAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/implementation_roadmap.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._build_pdf(state, output_path)
        state["roadmap_pdf_path"] = output_path
        return state

    def _build_pdf(self, state: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []
        req = state.get("requirements", {})
        est = state.get("estimation", {})

        # ── Banner ─────────────────────────────────────────────────────────
        banner = Table([[Paragraph(
            "Implementation Roadmap<br/><font size=13>Phase-wise Delivery Plan & Milestones</font>",
            s["cover_title"]
        )]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
            ("TOPPADDING",(0,0),(-1,-1),20),
            ("BOTTOMPADDING",(0,0),(-1,-1),20),
            ("LEFTPADDING",(0,0),(-1,-1),18),
        ]))
        st += [banner, Spacer(1,6),
               Paragraph(f"Project: Solar MES Implementation — {req.get('production_capacity','N/A')} | "
                         f"Total Duration: {est.get('total_duration_months','N/A')} months | "
                         f"{datetime.date.today().strftime('%d %B %Y')}", s["body"]),
               HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT), Spacer(1,12)]

        # ── 1. Summary Timeline ────────────────────────────────────────────
        st.append(Paragraph("1. Programme Summary", s["section_heading"]))
        phases = [
            ["Phase", "Name", "Duration", "Weeks", "Key Focus"],
            ["Phase 0", "Pre-Project Assessment", "4 weeks", "1–4",
             "Machine connectivity audit; SAP landscape; data quality; business case sign-off"],
            ["Phase 1", "Discovery & Blueprint", "8 weeks", "5–12",
             "AS-IS mapping; FSD; integration design; project charter; risk register"],
            ["Phase 2", "Core MES Configuration", "16 weeks", "13–28",
             "MES setup; QMS; genealogy; SAP integration; SFDC; unit testing"],
            ["Phase 3", "Equipment Integration", "16 weeks", "17–32",
             "OPC UA; Kafka; machine adapters (flash, EL, laminator, stringer); edge devices"],
            ["Phase 4", "PODISE / APS Deployment", "10 weeks", "21–30",
             "Scheduling engine; Gantt portal; lot splitting; SAP order dressing; parallel run"],
            ["Phase 5", "Testing & Go-Live", "8 weeks", "29–36",
             "UAT; load/DR/security test; pilot line go-live; 4-week hypercare"],
            ["Phase 6", "Expansion & Optimisation", "16 weeks", "37–52",
             "Roll to all lines; AI model training; ALMM automation; advanced analytics"],
        ]
        self._phase_table(st, phases, s)
        st.append(Spacer(1,10))

        # ── 2. Gantt-style visual (text-based) ────────────────────────────
        st.append(Paragraph("2. High-Level Gantt (52-Week View)", s["section_heading"]))
        st.append(Paragraph("Each block represents 4 weeks. ■ = active, □ = not started, ▶ = go-live milestone.", s["small"]))
        st.append(Spacer(1,6))
        gantt_data = [
            ["Phase / Activity", "Q1 (W1–12)", "Q2 (W13–24)", "Q3 (W25–36)", "Q4 (W37–52)"],
            ["Phase 0: Pre-Project",     "■■■□","□□□□","□□□□","□□□□"],
            ["Phase 1: Blueprint",       "■■■■","■■□□","□□□□","□□□□"],
            ["Phase 2: MES Config",      "□□□□","■■■■","■■■■","□□□□"],
            ["Phase 3: Equip. Integr.",  "□□□□","□■■■","■■■■","□□□□"],
            ["Phase 4: PODISE/APS",      "□□□□","□□■■","■■■□","□□□□"],
            ["Phase 5: Test & Go-Live ▶","□□□□","□□□□","□■■■","■□□□"],
            ["Phase 6: Expansion",       "□□□□","□□□□","□□□□","■■■■"],
        ]
        gantt_rows = []
        for i, row in enumerate(gantt_data):
            style = s["table_header"] if i == 0 else s["table_cell"]
            gantt_rows.append([Paragraph(str(c), style) for c in row])
        g_tbl = Table(gantt_rows, colWidths=[2.2*inch,1.1*inch,1.1*inch,1.1*inch,1.1*inch])
        g_tbl.setStyle(default_table_style())
        st.append(g_tbl)
        st.append(Spacer(1,12))

        # ── 3. Phase Detail Cards ──────────────────────────────────────────
        st.append(Paragraph("3. Phase-by-Phase Detail", s["section_heading"]))

        phase_details = [
            {
                "phase": "Phase 0", "name": "Pre-Project Assessment", "weeks": "Weeks 1–4",
                "activities": [
                    "Factory walk-through: all production lines, machines, network points",
                    "Machine connectivity audit: OPC UA readiness, PLC type, data availability per machine",
                    "SAP landscape assessment: version (ECC/S4), active modules, integration options",
                    "Data quality assessment: BOM completeness, routing accuracy, work center master",
                    "IT infrastructure review: server room, network topology, security policy",
                    "Business case finalisation: ROI model reviewed with CFO/COO",
                ],
                "deliverables": ["Connectivity audit report","SAP assessment report",
                                 "Infrastructure specification","Approved business case","Go/no-go decision"],
                "criteria": "Business case approved; budget allocated; project sponsor confirmed",
            },
            {
                "phase": "Phase 1", "name": "Discovery & Blueprint", "weeks": "Weeks 5–12",
                "activities": [
                    "AS-IS process mapping: all 11 solar manufacturing steps documented",
                    "Gap analysis: current state vs. target state per process area",
                    "Functional Specification Document (FSD): all MES modules, 200+ pages",
                    "Integration design specification: SAP (IDoc/REST), OPC UA (tag list per machine type), WMS",
                    "Data migration plan: master data from SAP/Excel, cleansing rules",
                    "Project charter, RACI matrix, risk register, change management plan",
                    "Training needs assessment: 60 operators + supervisors + IT team",
                ],
                "deliverables": ["AS-IS process maps","FSD (signed by all stakeholders)",
                                 "Integration design spec","Project charter","Risk register"],
                "criteria": "FSD signed by Plant Manager, IT Manager, Quality Manager, and SAP team",
            },
            {
                "phase": "Phase 2", "name": "Core MES Configuration", "weeks": "Weeks 13–28",
                "activities": [
                    "Work center, BOM, routing master data loading (from SAP export + cleansing)",
                    "Production order management configuration: lifecycle, status, priority rules",
                    "Shop floor UI design: operation-specific screens, barcode/tablet entry",
                    "QMS configuration: inspection plans, defect code library (IEC 61215 mapped), SPC charts",
                    "Material genealogy: lot traceability rules, serial number format, ALMM compliance fields",
                    "SAP integration: IDoc production order receipt, confirmation posting, GR/GI",
                    "OEE dashboard: Availability/Performance/Quality metrics, downtime reason codes",
                    "Unit testing: all 200+ test cases from FSD; defect resolution",
                ],
                "deliverables": ["Configured MES environment","SAP integration tested",
                                 "OEE dashboards live","QMS configured","Unit test report"],
                "criteria": "All unit tests passed; SAP round-trip test completed; UAT plan approved",
            },
            {
                "phase": "Phase 3", "name": "Equipment Integration", "weeks": "Weeks 17–32",
                "activities": [
                    "OPC UA tag mapping: all 20 machine types mapped to MES data model",
                    "Edge IoT gateway deployment: 1 per line, network config, OT VLAN setup",
                    "Kafka topic design: PDI/PDO, quality results, alarms, maintenance events",
                    "Flash tester integration: IV curve (Pmax, Voc, Isc, FF) per module serial",
                    "EL tester integration: AI image classification deployment, defect type mapping",
                    "Laminator temperature profile capture: set points vs. actuals per cycle",
                    "Stringer AOI integration: string count, ribbon consumption, solder quality",
                    "Interface testing: machine data vs. manual record validation (±2% tolerance)",
                ],
                "deliverables": ["All machines connected and validated","Kafka event flows verified",
                                 "AI EL classifier deployed","Interface test report"],
                "criteria": "Machine data validated against manual records; ±2% tolerance achieved for all machines",
            },
            {
                "phase": "Phase 4", "name": "PODISE / APS Deployment", "weeks": "Weeks 21–30",
                "activities": [
                    "Work center capacity model: shift calendar, break times, planned maintenance windows",
                    "Lot-size constraint configuration: laminator (max 12), flash tester (1), packaging (30)",
                    "Scheduling algorithm calibration: standard cycle times from Phase 3 actual data",
                    "SAP order dressing integration: VA01 sales order → PODISE → CO01 production order",
                    "Gantt dashboard deployment: Angular real-time; drag-and-drop override capability",
                    "Parallel run: PODISE schedule vs. manual planner (4 weeks); accuracy measurement",
                    "AI recommendations: plain-English rescheduling advice on rush orders / breakdowns",
                ],
                "deliverables": ["PODISE live on all work centers","Gantt portal deployed",
                                 "Parallel run report (>95% accuracy target)","Planner training complete"],
                "criteria": "PODISE schedule accuracy >95% vs. actual production; planner sign-off",
            },
            {
                "phase": "Phase 5", "name": "Testing & Go-Live", "weeks": "Weeks 29–36",
                "activities": [
                    "User Acceptance Testing (UAT): super-users test all FSD scenarios",
                    "Load testing: simulate peak day (120% of normal volume); performance validated",
                    "Disaster recovery test: failover to standby server; RTO measurement",
                    "Security penetration test: OT/IT segregation validated; auth tested",
                    "Parallel run: old system + MES side by side for 2–4 weeks on pilot line",
                    "Go-live: Line 1 pilot; 24/7 hypercare support for 4 weeks",
                    "OEE baseline captured: before/after comparison for business case validation",
                ],
                "deliverables": ["UAT sign-off","Load test report","DR test report",
                                 "Pilot line go-live","OEE baseline report"],
                "criteria": "Plant Manager sign-off on UAT; OEE baseline captured; no P1 open defects",
            },
            {
                "phase": "Phase 6", "name": "Expansion & Optimisation", "weeks": "Weeks 37–52",
                "activities": [
                    "Roll-out to remaining production lines (Lines 2, 3, 4) — 3-week each",
                    "AI model fine-tuning: EL classifier trained on plant-specific defect images",
                    "PODISE algorithm calibration: actual cycle times replace estimates",
                    "ALMM compliance module: serial registration, COC auto-generation live",
                    "Predictive maintenance: sensor baselines established; anomaly detection active",
                    "Advanced analytics: yield correlation, supplier quality, energy efficiency",
                    "Knowledge transfer: internal team capable of L2 support without vendor",
                ],
                "deliverables": ["All 4 lines live","ALMM COC automation","AI models optimised",
                                 "Knowledge transfer complete","Final project report"],
                "criteria": "All KPIs at or above target; internal team certified; project formally closed",
            },
        ]

        for pd in phase_details:
            self._phase_card(st, pd, s)
            st.append(Spacer(1,8))

        # ── 4. RACI Matrix ─────────────────────────────────────────────────
        st.append(Paragraph("4. RACI Matrix", s["section_heading"]))
        raci_data = [
            ["Activity","Vendor PM","Vendor Tech","Plant Mgr","IT Mgr","Production","Quality","SAP Team"],
            ["Business case","C","I","R/A","C","C","C","I"],
            ["Requirements (FSD)","R","C","A","C","C","C","C"],
            ["MES Configuration","R/A","R","I","C","C","C","I"],
            ["SAP Integration","C","R","I","C","I","I","R/A"],
            ["OPC UA Setup","R/A","R","I","C","I","I","I"],
            ["UAT Execution","C","C","A","C","R","R","C"],
            ["Training Delivery","R/A","C","I","I","C","C","I"],
            ["Go-Live Decision","C","C","R/A","C","C","C","C"],
            ["ALMM Compliance","C","R","I","I","I","R/A","I"],
        ]
        self._tbl(st, raci_data, s, [1.6*inch,0.7*inch,0.8*inch,0.7*inch,0.6*inch,0.9*inch,0.7*inch,0.7*inch])
        st.append(Paragraph("R=Responsible, A=Accountable, C=Consulted, I=Informed", s["small"]))
        st.append(Spacer(1,10))

        # ── 5. Key Milestones ─────────────────────────────────────────────
        st.append(Paragraph("5. Key Project Milestones", s["section_heading"]))
        milestone_data = [
            ["Milestone","Target Week","Success Criteria","Owner"],
            ["M0: Project Kick-off","Week 1","All stakeholders aligned; project plan signed","Vendor PM"],
            ["M1: FSD Sign-off","Week 12","All 200+ requirements approved by all stakeholders","Plant Mgr"],
            ["M2: Integration Design Approved","Week 12","SAP, OPC UA, Kafka specs approved by IT & SAP teams","IT Mgr"],
            ["M3: MES Unit Test Complete","Week 28","All test cases passed; zero P1 defects open","Vendor PM"],
            ["M4: Machine Integration Validated","Week 32","All machines data-validated; ±2% tolerance met","Vendor Tech"],
            ["M5: PODISE Parallel Run Complete","Week 30",">95% scheduling accuracy vs. actual","Production"],
            ["M6: UAT Sign-off","Week 34","All super-users sign off; zero P1 defects","Plant Mgr"],
            ["M7: Pilot Line Go-Live ▶","Week 36","Line 1 live; OEE visible; no critical issues","Plant Mgr"],
            ["M8: All Lines Live","Week 50","All 4 lines operational; ALMM COC automated","Plant Mgr"],
            ["M9: Project Closure","Week 52","KPIs validated; knowledge transfer complete","Vendor PM"],
        ]
        self._tbl(st, milestone_data, s, [2.0*inch,1.0*inch,2.3*inch,1.2*inch])

        doc.build(st)

    def _phase_table(self, story, data, s):
        rows = []
        for i, row in enumerate(data):
            if i == 0:
                rows.append([Paragraph(c, s["table_header"]) for c in row])
            else:
                phase_key = row[0]
                bg = _PHASE_COLORS.get(phase_key, colors.white)
                rows.append([Paragraph(c, s["table_cell"]) for c in row])
        tbl = Table(rows, colWidths=[0.7*inch,1.7*inch,0.9*inch,0.6*inch,2.7*inch])
        ts = default_table_style()
        for i in range(1, len(data)):
            bg = _PHASE_COLORS.get(data[i][0], colors.white)
            ts.add("BACKGROUND", (0,i), (0,i), bg)
        tbl.setStyle(ts)
        story.append(tbl)

    def _phase_card(self, story, pd: dict, s):
        phase = pd["phase"]
        bg = _PHASE_COLORS.get(phase, BRAND_LIGHT)
        header_data = [[
            Paragraph(f"<b>{phase}: {pd['name']}</b>", s["sub_heading"]),
            Paragraph(pd["weeks"], s["body"]),
        ]]
        header_tbl = Table(header_data, colWidths=[5.0*inch,1.5*inch])
        header_tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),bg),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("BOX",(0,0),(-1,-1),0.5,BRAND_MID),
        ]))
        story.append(header_tbl)

        # Activities
        for act in pd["activities"]:
            story.append(Paragraph(f"  • {act}", s["body"]))

        # Deliverables + criteria
        delivs = " | ".join(pd["deliverables"])
        story.append(Paragraph(f"<b>Deliverables:</b> {delivs}", s["small"]))
        story.append(Paragraph(f"<b>Go/No-Go Criteria:</b> {pd['criteria']}", s["small"]))

    def _tbl(self, story, data, s, widths):
        rows = [[Paragraph(str(c), s["table_header"] if i==0 else s["table_cell"])
                 for c in row] for i, row in enumerate(data)]
        tbl = Table(rows, colWidths=widths)
        tbl.setStyle(default_table_style())
        story.append(tbl)