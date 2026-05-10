"""
agents/proposal_agent.py
-------------------------
Professional, comprehensive 14‑section MES / APS / WMS Solution Proposal.
Includes all sections expected by solar manufacturing customers.
"""
import datetime, os, re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID,
    get_styles, default_table_style, strip_markdown, nl2br,
)
# We'll import get_llm to optionally enrich sections with AI-generated text
from llm_factory import get_llm

class ProposalAgent:
    def __init__(self):
        self.s = get_styles()
        self.llm = get_llm(temperature=0.3)   # For discrete enrichment tasks

    def _fmt_req(self, req_obj) -> str:
        if isinstance(req_obj, str): return req_obj
        if isinstance(req_obj, dict):
            title = req_obj.get("requirement", "") or req_obj.get("title", "")
            details = req_obj.get("details", [])
            if isinstance(details, list) and details:
                return f"{title} ({'; '.join(details)})"
            return title
        return str(req_obj)

    def run(self, state: dict, output_path: str = "output/proposal.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []
        req = state.get("requirements", {})
        est = state.get("estimation", {})
        roi = est.get("roi", {})
        domain = strip_markdown(state.get("domain_knowledge", ""))
        roi_know = strip_markdown(state.get("roi_knowledge", ""))

        # ── COVER PAGE ────────────────────────────────────────────────────────
        banner = Table([[Paragraph("Comprehensive MES / APS / WMS Solution Proposal<br/>"
                                   "<font size=14>Solar Manufacturing Digital Transformation</font>",
                                   s["cover_title"])]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
                                    ("TOPPADDING",(0,0),(-1,-1),24),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),24),
                                    ("LEFTPADDING",(0,0),(-1,-1),18)]))
        st.append(banner); st.append(Spacer(1,6))
        today = datetime.date.today().strftime("%d %B %Y")
        st.append(Paragraph(f"Prepared for: {req.get('industry','Solar')} Manufacturer | Date: {today}", s["body"]))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT)); st.append(Spacer(1,14))

        # ── 1. EXECUTIVE SUMMARY ──────────────────────────────────────────────
        st.append(Paragraph("1. Executive Summary", s["section_heading"]))
        summary = (
            f"This proposal presents an AI‑native Manufacturing Execution System (MES), "
            f"Advanced Planning & Scheduling (APS), and Warehouse Management System (WMS) "
            f"tailored for {req.get('industry','solar')} panel manufacturing. "
            f"The solution addresses current pain points – {', '.join(req.get('pain_points',['manual tracking']))} – "
            f"and delivers real‑time production visibility, intelligent scheduling, "
            f"ALMM‑compliant traceability, and dispatch optimisation."
        )
        st.append(Paragraph(summary, s["body"])); st.append(Spacer(1,12))

        # ── 2. CUSTOMER REQUIREMENTS ──────────────────────────────────────────
        st.append(Paragraph("2. Customer Requirements", s["section_heading"]))
        fields = [
            ("Industry", req.get("industry","N/A")),("Product", req.get("product","N/A")),
            ("Production Capacity", req.get("production_capacity","N/A")),
            ("Production Lines", str(req.get("lines","N/A"))),("Machine Types", str(req.get("machine_types","N/A"))),
            ("ERP System", str(req.get("erp") or "None")),
            ("Current Systems", ", ".join(req.get("current_systems",[])) or "None listed"),
            ("Customisation Level", req.get("customization","medium").title()),
        ]
        req_tbl = Table([[Paragraph(k,s["table_header"]),Paragraph(v,s["table_cell"])] for k,v in fields],
                        colWidths=[2.0*inch,4.5*inch])
        req_tbl.setStyle(default_table_style()); st.append(req_tbl); st.append(Spacer(1,8))
        pain_points = req.get("pain_points",[])
        if pain_points:
            st.append(Paragraph("Pain Points:", s["sub_heading"]))
            for pp in pain_points: st.append(Paragraph(f"• {pp}", s["body"]))
        st.append(Spacer(1,8))
        reqs = req.get("requirements",[])
        if reqs:
            st.append(Paragraph("Functional Requirements:", s["sub_heading"]))
            rows = [[Paragraph("#",s["table_header"]),Paragraph("Requirement",s["table_header"])]]
            for i, r in enumerate(reqs, 1):
                rows.append([Paragraph(str(i),s["table_cell"]),Paragraph(self._fmt_req(r),s["table_cell"])])
            t = Table(rows, colWidths=[0.4*inch,6.1*inch]); t.setStyle(default_table_style()); st.append(t)
        st.append(Spacer(1,12))

        # ── 3. INDUSTRY BEST PRACTICES ────────────────────────────────────────
        st.append(Paragraph("3. Industry Best Practices & Recommendations", s["section_heading"]))
        st.append(Paragraph(nl2br(domain[:2000] if domain else "MES best practices per solar domain."), s["body"]))
        st.append(Spacer(1,12))

        # ── 4. MES FUNCTIONAL SCOPE ───────────────────────────────────────────
        st.append(Paragraph("4. MES Functional Scope", s["section_heading"]))
        st.append(Paragraph(
            "The solution covers the entire manufacturing lifecycle, from order receipt to dispatch. "
            "Below is a summary of the key modules and their solar‑specific capabilities.",
            s["body"]))
        st.append(Spacer(1,6))

        mes_modules = [
            ("Order Management", "Import sales orders from SAP, prioritise (govt vs commercial), manage delivery dates, generate production batches."),
            ("Production Planning (Projection)", "Weekly demand projection, capacity simulation, line allocation, material requirement planning (MRP)."),
            ("Order Scheduler", "Allocate orders to production lines, prioritise urgent/tender orders, minimise changeover time, provide suggested start dates."),
            ("Line Scheduler", "Finite‑capacity scheduling per work centre; batch‑aware (laminator: 12, flash tester: 1, packaging: 30); real‑time Gantt; automatic re‑optimisation on disruptions."),
            ("Production Tracking", "Real‑time OEE, machine status, production counts; integration via OPC UA, MQTT, Modbus; scrap alerts and cycle‑time monitoring."),
            ("Quality Management", "AI‑AOI inspection, EL image classification, flash test capture, material genealogy (ingot→wafer→cell→module), ALMM compliance dashboards."),
            ("Warehouse Management (WMS)", "Raw material, WIP, finished goods inventory; LPN scanning, location tracking, FEFO for EVA/backsheet expiry, dock‑to‑dock visibility."),
            ("Dispatch Planning", "Pallet grouping, route‑based loading, digital packing list, ALMM Certificate of Compliance (COC) auto‑generation."),
            ("Truck Scheduling", "Optimises dock allocation and truck arrival times to reduce waiting, improve fill rates, and cut logistics cost."),
        ]
        mod_rows = [[Paragraph("Module", s["table_header"]), Paragraph("Description", s["table_header"])]]
        for mod, desc in mes_modules:
            mod_rows.append([Paragraph(mod, s["table_cell"]), Paragraph(desc, s["table_cell"])])
        mod_tbl = Table(mod_rows, colWidths=[2.0*inch, 4.5*inch])
        mod_tbl.setStyle(default_table_style()); st.append(mod_tbl)
        st.append(Spacer(1,12))

        # ── 5. APS / PODISE DETAIL ────────────────────────────────────────────
        st.append(Paragraph("5. Advanced Planning & Scheduling (PODISE/APS)", s["section_heading"]))
        st.append(Paragraph(
            "Traditional SAP MRP cannot handle solar‑specific lot sizing, half‑cut cell batching, "
            "or bifacial routing. PODISE fills this gap with real‑time, constraint‑based scheduling.",
            s["body"]))
        st.append(Spacer(1,6))
        aps_compare = [
            ["Capability", "SAP MRP", "PODISE/APS"],
            ["Scheduling granularity", "Day‑level", "Hour / minute level"],
            ["Capacity handling", "Infinite capacity", "Finite capacity"],
            ["Rush order response", "Batch run (1+ hour)", "< 30 seconds automated"],
            ["Lot‑size constraints", "Basic min/max", "Multi‑level (solar‑specific)"],
            ["Technology variants", "Limited BOM", "Full PERC/TOPCon/Bifacial/HJT"],
            ["Bottleneck visibility", "None", "Real‑time identification"],
            ["Re‑optimisation on breakdown", "Manual replanning", "Automatic on Kafka event"],
            ["Gantt visualisation", "None", "Real‑time Angular Gantt (drag‑drop)"],
            ["AI recommendations", "None", "Plain‑English rescheduling advice"],
        ]
        aps_tbl = Table([[Paragraph(c, s["table_header"]) for c in aps_compare[0]]] +
                        [[Paragraph(c, s["table_cell"]) for c in row] for row in aps_compare[1:]],
                        colWidths=[2.4*inch, 2.0*inch, 2.1*inch])
        aps_tbl.setStyle(default_table_style()); st.append(aps_tbl)
        st.append(Spacer(1,6))
        # Include a sample scenario
        st.append(Paragraph(
            "<b>Example:</b> When laminator #2 breaks down, PODISE re‑optimises all affected orders within 30 seconds, "
            "reassigning batches to other laminators and providing an updated delivery forecast to SAP and the Gantt dashboard.",
            s["body"]))
        st.append(Spacer(1,12))

        # ── 6. SYSTEM ARCHITECTURE ────────────────────────────────────────────
        st.append(Paragraph("6. System Architecture", s["section_heading"]))
        diagram = state.get("diagram_image_path")
        if diagram and os.path.exists(diagram):
            try:
                st.append(Image(os.path.abspath(diagram), width=5.5*inch, height=3.2*inch))
                st.append(Spacer(1,6))
            except Exception as exc: print(f"⚠️ Diagram embed error: {exc}")
        arch = strip_markdown(state.get("architecture", "See High‑Level Design document for full details."))
        st.append(Paragraph(nl2br(arch[:1500]), s["body"]))
        st.append(Paragraph("<i>For a detailed diagram, refer to the High‑Level Design (HLD) document.</i>", s["small"]))
        st.append(Spacer(1,12))

        # ── 7. INTEGRATION ARCHITECTURE ───────────────────────────────────────
        st.append(Paragraph("7. Integration Architecture", s["section_heading"]))
        integration_table = [
            ["Integration", "Direction", "Protocol", "Frequency", "Data Exchanged"],
            ["SAP ERP ↔ MES", "Bidirectional", "REST API / IDoc", "Real‑time / Hourly", "Sales orders, BOM, routings, confirmations, quality results"],
            ["MES ↔ OPC UA Gateway", "Bidirectional", "OPC UA", "1‑5 seconds", "Machine commands, sensor data, status, alarms"],
            ["OPC UA Gateway → Kafka", "Unidirectional", "OPC UA subscription", "Continuous", "Timestamped tag values"],
            ["Kafka → PostgreSQL / InfluxDB", "Unidirectional", "Kafka Consumer", "Continuous", "PDI/PDO records, sensor time‑series"],
            ["MES ↔ WMS", "Bidirectional", "REST API", "Event‑driven", "Pick instructions, inventory confirmations, LPN data"],
            ["MES → ALMM Portal", "Unidirectional", "REST API (MNRE)", "On dispatch", "Module serial, test results, COC"],
            ["Quality Inspection Agent → PostgreSQL", "Unidirectional", "Kafka / REST", "Every test cycle", "EL classification, flash test IV curves, defect codes"],
        ]
        int_tbl = Table([[Paragraph(c, s["table_header"]) for c in integration_table[0]]] +
                        [[Paragraph(c, s["table_cell"]) for c in row] for row in integration_table[1:]],
                        colWidths=[1.6*inch, 1.1*inch, 1.2*inch, 1.0*inch, 1.8*inch])
        int_tbl.setStyle(default_table_style()); st.append(int_tbl)
        st.append(Spacer(1,12))

        # ── 8. ROLE OF AI AGENTS ──────────────────────────────────────────────
        st.append(Paragraph("8. AI‑Native Multi‑Agent System", s["section_heading"]))
        st.append(Paragraph(
            "Nine specialised AI agents coordinate via Kafka and MCP tools, powered by on‑premises Ollama + Llama 3.2. "
            "This ensures data sovereignty and intelligent automation at every step.",
            s["body"]))
        ai_agents = [
            ["Agent", "Role", "AI Capability"],
            ["Orchestrator", "Goal decomposition, workflow coordination", "Fault‑tolerant task sequencing"],
            ["PODISE / APS", "Sales order → production order; lot splitting; scheduling", "Constraint‑based optimisation; real‑time re‑planning"],
            ["PDI/PDO Tracking", "Machine data ingestion (OPC UA, MQTT, Excel)", "Scrap analysis, cycle‑time anomaly detection"],
            ["Quality Inspection", "AI‑AOI + EL classification + flash test capture", "CNN defect detection >98% accuracy"],
            ["Predictive Maintenance", "Sensor stream analysis, failure forecast", "MTBF prediction, PM work order creation"],
            ["Dispatch Planning", "AI‑optimised truck loading, dock assignment", "Route optimisation, fill‑rate maximisation"],
            ["Reporting", "Shift‑end summaries, plain‑English AI narration", "LLM‑generated management reports"],
        ]
        ai_tbl = Table([[Paragraph(c, s["table_header"]) for c in ai_agents[0]]] +
                       [[Paragraph(c, s["table_cell"]) for c in row] for row in ai_agents[1:]],
                       colWidths=[1.8*inch, 2.8*inch, 2.0*inch])
        ai_tbl.setStyle(default_table_style()); st.append(ai_tbl)
        st.append(Spacer(1,12))

        # ── 9. IMPLEMENTATION PHASES & ROADMAP ────────────────────────────────
        st.append(Paragraph("9. Implementation Phases & Roadmap", s["section_heading"]))
        phases = [
            ("Phase 1 – Foundation (Weeks 1‑8)", "AS‑IS mapping, GAP analysis, blueprint sign‑off, MES core configuration, basic SFDC."),
            ("Phase 2 – Planning & APS (Weeks 9‑20)", "PODISE/APS deployment, line scheduler, Gantt dashboard, SAP integration."),
            ("Phase 3 – Warehouse & Dispatch (Weeks 16‑28)", "WMS go‑live (inbound, inventory, outbound), dispatch planning, ALMM COC."),
            ("Phase 4 – Equipment Integration & AI (Weeks 12‑32)", "OPC UA connectivity, PDI/PDO agents, AI–AOI, predictive maintenance."),
            ("Phase 5 – Testing & Go‑Live (Weeks 28‑36)", "UAT, parallel run, operator training, go‑live (line‑by‑line), hypercare."),
            ("Phase 6 – Optimisation & Expansion (Weeks 36‑52)", "KPI monitoring, AI model tuning, remaining line rollout, ALMM compliance automation."),
        ]
        for title, desc in phases:
            st.append(Paragraph(f"<b>{title}:</b> {desc}", s["body"]))
        st.append(Spacer(1,12))

        # ── 10. EFFORT & COST ESTIMATION ──────────────────────────────────────
        st.append(Paragraph("10. Effort & Cost Estimation", s["section_heading"]))
        est_rows = [
            [Paragraph("Total Effort (person‑months)", s["table_header"]), Paragraph(str(est.get("total_effort_person_months","N/A")), s["table_cell"])],
            [Paragraph("Total Duration (months)", s["table_header"]), Paragraph(str(est.get("total_duration_months","N/A")), s["table_cell"])],
            [Paragraph("Estimated Cost (USD)", s["table_header"]), Paragraph(f"${est.get('estimated_cost_usd',0):,.0f}", s["table_cell"])],
        ]
        s_tbl = Table(est_rows, colWidths=[3.0*inch,3.5*inch]); s_tbl.setStyle(default_table_style()); st.append(s_tbl)
        phase_breakdown = est.get("phase_breakdown",{})
        if phase_breakdown:
            st.append(Paragraph("Phase Breakdown:", s["sub_heading"]))
            ph_rows = [[Paragraph("Phase",s["table_header"]),Paragraph("Duration",s["table_header"])]]
            for phase,dur in phase_breakdown.items():
                ph_rows.append([Paragraph(phase,s["table_cell"]),Paragraph(str(dur),s["table_cell"])])
            ph_tbl = Table(ph_rows, colWidths=[4.0*inch,2.5*inch]); ph_tbl.setStyle(default_table_style()); st.append(ph_tbl)
        st.append(Spacer(1,12))

        # ── 11. ROI & BUSINESS CASE ───────────────────────────────────────────
        st.append(Paragraph("11. ROI & Business Case", s["section_heading"]))
        annual_savings = roi.get("annual_savings_usd",0)
        total_cost = est.get("estimated_cost_usd",0)
        five_yr_net = (annual_savings*5)-total_cost
        roi_rows = [
            ["Metric","Value"],
            ["Total Investment",f"${total_cost:,.0f}"],
            ["Annual Savings",f"${annual_savings:,.0f}"],
            ["Payback Period",f"{roi.get('payback_months','N/A')} months"],
            ["5‑Year Net Benefit",f"${five_yr_net:,.0f}"],
            ["Efficiency Gain",f"{roi.get('efficiency_gain_pct','N/A')}%"],
            ["OEE Improvement",f"{roi.get('oee_improvement_pct','N/A')}%"],
            ["Quality Cost Reduction",f"{roi.get('quality_cost_reduction_pct','N/A')}%"],
        ]
        roi_tbl = Table([[Paragraph(r[0], s["table_header"]), Paragraph(r[1], s["table_cell"])] for r in roi_rows],
                        colWidths=[3.0*inch,3.5*inch])
        roi_tbl.setStyle(default_table_style()); st.append(roi_tbl)
        if roi_know:
            st.append(Spacer(1,8)); st.append(Paragraph("Industry Benchmarks:", s["sub_heading"]))
            st.append(Paragraph(nl2br(roi_know[:1200]), s["body"]))
        st.append(Spacer(1,12))

        # ── 12. COMMERCIAL MODEL ──────────────────────────────────────────────
        st.append(Paragraph("12. Commercial Model", s["section_heading"]))
        st.append(Paragraph(
            "<b>License Model:</b> Annual subscription or perpetual license with annual maintenance (AMC).<br/>"
            "<b>Implementation Services:</b> Fixed‑price phased approach; billed per phase upon milestone completion.<br/>"
            "<b>Team Structure:</b> Program Manager, Solution Architect, MES Consultant, APS Expert, Integration Engineer, QA Lead.<br/>"
            "<b>Support:</b> 24×7 hypercare for 4 weeks post go‑live; optional extended support SLA.<br/>"
            "<b>Infrastructure:</b> On‑premise servers, GPU for AI, edge gateways – detailed in HLD.<br/>"
            "<b>Training:</b> Hands‑on operator training at workstations, supervisor dashboards, management analytics.",
            s["body"]))
        st.append(Spacer(1,12))

        # ── 13. RISK ASSESSMENT (link) ─────────────────────────────────────────
        st.append(Paragraph("13. Risk Assessment", s["section_heading"]))
        st.append(Paragraph(
            "A comprehensive Risk Assessment Report is provided as a separate document. "
            "The top risks include integration complexity, machine data availability, user adoption, and schedule slippage. "
            "Mitigation plans are detailed in the risk register.",
            s["body"]))
        st.append(Spacer(1,12))

        # ── 14. NEXT STEPS ────────────────────────────────────────────────────
        st.append(Paragraph("14. Next Steps", s["section_heading"]))
        for i,step in enumerate([
            "Customer reviews this proposal and provides written acceptance.",
            "Kick‑off meeting within 2 weeks of acceptance.",
            "Phase 1 (Discovery & Blueprint) commences with dedicated team.",
            "Detailed project plan, RACI matrix, and risk register delivered by end of Phase 1.",
            "Pilot line go‑live (MES + APS) within 20 weeks; subsequent lines rolled out iteratively.",
        ],1):
            st.append(Paragraph(f"{i}. {step}", s["body"]))
        st.append(Spacer(1,14))
        st.append(HRFlowable(width="100%", thickness=1, color=BRAND_MID))
        st.append(Spacer(1,6))
        st.append(Paragraph("Proposal valid 30 days. Costs indicative – final scoping during Phase 1.", s["small"]))

        doc.build(st)
        state["proposal_pdf_path"] = output_path
        return state