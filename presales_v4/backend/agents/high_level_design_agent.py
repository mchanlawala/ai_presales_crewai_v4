"""
agents/high_level_design_agent.py
-----------------------------------
Generates a professional High-Level Design (HLD) document PDF covering:
  1. System Architecture Overview (with diagram)
  2. Component Architecture (each system described)
  3. APS / PODISE Design Detail
  4. Multi-Agent AI System Design
  5. Integration Architecture (SAP ↔ MES ↔ OPC UA ↔ WMS)
  6. Data Flow Diagram
  7. Deployment Architecture
  8. Security Architecture

Result → state["hld_pdf_path"]
"""
import datetime
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from langchain_core.messages import HumanMessage

from llm_factory import get_llm
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_LIGHT, BRAND_MID,
    get_styles, default_table_style, strip_markdown, nl2br,
)
from diagram_utils import render_plantuml


# ── PlantUML diagrams ─────────────────────────────────────────────────────────

_SYSTEM_ARCH_DIAGRAM = """@startuml
skinparam componentStyle rectangle
skinparam backgroundColor #FAFAFA
skinparam defaultFontName Arial
skinparam component {
  BackgroundColor #EAF2FB
  BorderColor #2E6DA4
  FontColor #1A2E44
}

package "Customer Layer" {
  component "Angular Portal\\n(Operator UI)" as ui
  component "Management\\nDashboards" as dash
  component "Mobile App\\n(Operator)" as mobile
}

package "AI Agent Orchestration Layer" {
  component "Orchestrator\\nAgent" as orch
  component "PODISE /\\nAPS Agent" as podise
  component "PDI/PDO\\nTracking Agent" as pdi
  component "Quality\\nInspection Agent" as qa
  component "Predictive Maint.\\nAgent" as pma
  component "Dispatch\\nPlanning Agent" as dispatch
  component "Reporting\\nAgent" as rep
}

package "Core MES Platform" {
  component "Production Order\\nManagement" as pom
  component "Shop Floor DC\\n(SFDC)" as sfdc
  component "Quality Mgmt\\n(QMS)" as qms
  component "Material Genealogy\\n& Traceability" as mat
  component "WIP Tracking &\\nOEE" as oee
}

package "Integration Layer" {
  component "SAP ERP\\n(SD/PP/MM/QM)" as sap
  component "OPC UA Gateway" as opcua
  component "Kafka Event Bus" as kafka
  component "WMS" as wms
}

package "Data Layer" {
  component "PostgreSQL\\n(Transactional)" as pg
  component "InfluxDB\\n(Time-Series)" as influx
  component "AI Model Store\\n(Ollama + Llama 3.2)" as ai
  component "Document Store\\n(EL Images, COC)" as docs
}

package "Shop Floor (L0-L2)" {
  component "Flash Tester" as flash
  component "EL Tester" as el
  component "Laminator" as lam
  component "Stringer" as str_m
  component "SCADA / PLC" as scada
}

ui --> orch : Operator actions
dash --> rep : KPI requests
mobile --> sfdc : PDI/PDO entry
orch --> podise : Schedule request
orch --> pdi : Track production
orch --> qa : Quality check
orch --> pma : Maintenance check
podise --> sap : Prod orders (REST/IDoc)
podise --> kafka : Schedule events
pdi --> kafka : Raw operation logs
kafka --> pg : Persist records
kafka --> influx : Sensor time-series
qa --> ai : Image classification
qa --> docs : Store EL images
pma --> influx : Sensor analysis
dispatch --> wms : Shipment instructions
rep --> pg : Analytics queries
pom --> sap : Order confirmation
mat --> pg : Genealogy records
opcua --> kafka : Real-time machine data
scada --> opcua : Sensor & status data
flash --> opcua : IV curve data
el --> opcua : EL test results
lam --> opcua : Temperature profiles
str_m --> opcua : String data
sap --> pom : Production orders
@enduml"""


_PODISE_FLOW_DIAGRAM = """@startuml
skinparam backgroundColor #FAFAFA
title PODISE — Sales Order to Shop Floor Schedule Flow
start
:Sales Order Received (VA01 / API);
:ATP Check (Available to Promise);
if (ATP sufficient?) then (yes)
  :Reserve stock;
  :Confirm delivery date to customer;
else (no)
  :MRP Calculation;
  :Generate Planned Orders;
  :Convert to Production Orders;
endif
:BOM Explosion\\n(Technology-variant: PERC/TOPCon/Bifacial);
:Routing Selection\\n(Half-cut: doubled cell count);
:Backward Scheduling\\n(from delivery date);
if (Backward start < today?) then (yes)
  :Forward Scheduling\\n(from earliest available);
else (no)
  :Use backward schedule;
endif
:Finite Capacity Check\\n(bottleneck work centers);
:Lot Splitting\\n(Laminator:12, Flash:1, Pack:30);
:Gantt Generation;
:Publish to Kafka\\n(line schedule events);
:Push to Angular Portal\\n(real-time WebSocket);
:Notify Supervisors\\n(AI-generated plain English);
stop
@enduml"""


_INTEGRATION_DIAGRAM = """@startuml
skinparam backgroundColor #FAFAFA
title Integration Architecture — Solar MES

component "SAP ERP\\n(SD/PP/MM/QM)" as sap
component "Solar MES" as mes
component "PODISE Engine" as podise
component "OPC UA Gateway" as opcua
component "Kafka Event Bus" as kafka
component "WMS Platform" as wms
component "ALMM Portal\\n(MNRE)" as almm
component "PostgreSQL" as pg
component "InfluxDB" as influx

sap --> podise : Production Orders, BOM, Routing\\n(IDoc / REST API — bidirectional, batch)
podise --> sap : Order Confirmations, Actual Quantities\\n(CO11N / MIGO — hourly batch)
mes --> sap : Quality Results, GR/GI\\n(REST/IDoc — event-driven)
sap --> mes : Material Master, Customer Orders\\n(REST — on change)

mes --> opcua : Machine Commands, Parameter Setpoints\\n(OPC UA — real-time)
opcua --> kafka : Sensor Data, Status, Quality Results\\n(OPC UA subscription — 1-5s)
kafka --> pg : All MES Events\\n(Kafka Consumer — persistent)
kafka --> influx : Time-series Machine Data\\n(Kafka Consumer — continuous)

mes --> wms : Pick Instructions, GI/GR triggers\\n(REST API — event-driven)
wms --> mes : Inventory Confirmation, Batch Locations\\n(REST API — real-time)

mes --> almm : Module Serial + Test Results\\n(REST API — on dispatch)
@enduml"""


_AGENT_DESIGN_DIAGRAM = """@startuml
skinparam backgroundColor #FAFAFA
title Multi-Agent AI System — Solar MES

agent "Customer / ERP" as customer

package "Orchestrator Layer" {
  agent "Orchestrator Agent\\n(Temporal.io + LangChain4j)" as orch
}

package "Domain Agents" {
  agent "Prod. Order Design\\nAgent" as pod
  agent "PODISE / APS\\nAgent" as aps
  agent "Line Scheduler\\nAgent" as ls
  agent "Material Allocation\\nAgent" as mat
  agent "PDI/PDO Tracking\\nAgent" as pdi
  agent "Quality Inspection\\nAgent (AI-AOI/EL)" as qa
  agent "Predictive Maint.\\nAgent" as pma
  agent "Dispatch Planning\\nAgent" as dispatch
  agent "Reporting Agent\\n(AI Shift Summary)" as rep
}

package "AI Infrastructure" {
  database "Ollama + Llama 3.2\\n(On-premises GPU)" as llm
  database "MCP Tool Registry" as mcp
  database "PostgreSQL\\n(Workflow State)" as pg
}

customer --> orch : High-level goal
orch --> pod : Design order
orch --> aps : Schedule
orch --> pdi : Track production
orch --> qa : Inspect quality
orch --> pma : Predict maintenance
orch --> dispatch : Plan dispatch
orch --> rep : Generate report
pod --> mcp : SAP BAPI tools
aps --> mcp : Capacity tools
pdi --> mcp : OPC UA / Kafka tools
qa --> llm : Image classification
rep --> llm : Natural language generation
mat --> mcp : SAP BAPI_GOODSMVT_CREATE
orch --> pg : Persist workflow state
@enduml"""


class HighLevelDesignAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/high_level_design.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate diagrams
        diagrams = self._generate_diagrams()

        # Build PDF
        self._build_pdf(state, diagrams, output_path)
        state["hld_pdf_path"] = output_path
        return state

    # ── Diagram generation ────────────────────────────────────────────────────

    def _generate_diagrams(self) -> dict:
        diagram_map = {
            "system_arch":   (_SYSTEM_ARCH_DIAGRAM,    "hld_system_arch.png"),
            "podise_flow":   (_PODISE_FLOW_DIAGRAM,    "hld_podise_flow.png"),
            "integration":   (_INTEGRATION_DIAGRAM,    "hld_integration.png"),
            "agent_design":  (_AGENT_DESIGN_DIAGRAM,   "hld_agent_design.png"),
        }
        paths = {}
        for key, (code, fname) in diagram_map.items():
            try:
                path = render_plantuml(code, filename=fname)
                paths[key] = path
                print(f"   ✓ HLD diagram: {fname}")
            except Exception as exc:
                print(f"   ⚠️  HLD diagram {fname} failed: {exc}")
                paths[key] = None
        return paths

    # ── PDF builder ────────────────────────────────────────────────────────────

    def _build_pdf(self, state: dict, diagrams: dict, path: str):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40,
        )
        s, st = self.s, []
        req = state.get("requirements", {})
        est = state.get("estimation", {})

        # ── Cover ──────────────────────────────────────────────────────────────
        banner = Table([[Paragraph(
            "High-Level Design Document<br/><font size=13>Solar MES — AI-Native Architecture</font>",
            s["cover_title"]
        )]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), BRAND_DARK),
            ("TOPPADDING",    (0,0), (-1,-1), 22),
            ("BOTTOMPADDING", (0,0), (-1,-1), 22),
            ("LEFTPADDING",   (0,0), (-1,-1), 18),
        ]))
        st.append(banner); st.append(Spacer(1, 6))
        st.append(Paragraph(
            f"Project: MES Implementation — {req.get('industry','Solar')} Manufacturing  |  "
            f"Date: {datetime.date.today().strftime('%d %B %Y')}",
            s["body"]
        ))
        st.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT))
        st.append(Spacer(1, 14))

        # ── 1. System Architecture Overview ───────────────────────────────────
        st.append(Paragraph("1. System Architecture Overview", s["section_heading"]))
        st.append(Paragraph(
            "The Solar MES is an AI-native, event-driven manufacturing execution platform. "
            "It integrates SAP ERP with shop-floor machines via an intelligent multi-agent "
            "orchestration layer, providing real-time production tracking, ALMM-compliant "
            "traceability, AI-powered quality inspection, and intelligent scheduling through PODISE.",
            s["body"]
        ))
        st.append(Spacer(1, 8))
        self._embed_diagram(st, diagrams.get("system_arch"), "System Architecture Diagram", s, w=6.0, h=4.5)
        st.append(Spacer(1, 12))

        # ── 2. System Components ──────────────────────────────────────────────
        st.append(Paragraph("2. System Components", s["section_heading"]))
        components = [
            ["Component", "Role", "Technology"],
            ["SAP ERP (SD/PP/MM/QM)", "Production orders, BOM, finance, procurement", "SAP S/4HANA or ECC"],
            ["Solar MES Platform", "Core execution: order mgmt, SFDC, QMS, OEE, traceability", "Java Spring Boot + Kafka"],
            ["PODISE / APS Engine", "Real-time sales→production order conversion; lot splitting; scheduling", "Java + Temporal.io + Ollama"],
            ["Line Scheduler", "Finite-capacity Gantt; WebSocket push to UI; batch-aware", "Java + Angular"],
            ["PDI/PDO Tracking Agent", "OPC UA/MQTT/Excel ingest → Kafka → PostgreSQL; AI insights", "Python + LangChain4j + Kafka"],
            ["Quality Inspection Agent", "EL/AOI image classification; flash test capture; defect coding", "Python + CNN + Ollama"],
            ["Predictive Maint. Agent", "Sensor stream analysis; failure forecast; maintenance WO creation", "Python + InfluxDB + Ollama"],
            ["OPC UA Gateway", "L2↔L3 machine data bridge; tag mapping; subscription model", "Kepware / Ignition / machine-native"],
            ["Kafka Event Bus", "Event backbone; decoupling; replay; horizontal scaling", "Apache Kafka + Zookeeper"],
            ["PostgreSQL", "Transactional data; audit trail; workflow state; genealogy", "PostgreSQL 15+"],
            ["InfluxDB", "Time-series sensor data; OEE metrics; trend analysis", "InfluxDB 2.x"],
            ["Angular Portal", "Operator UI; Gantt; OEE dashboards; quality alerts; shift reports", "Angular 17 + WebSocket"],
            ["AI Inference (Ollama)", "On-premises LLM; Llama 3.2; image classification; NL reports", "Ollama + GPU server"],
            ["MCP Tool Registry", "Uniform tool interface for agents to call SAP, Kafka, OPC UA, JDBC", "Model Context Protocol"],
            ["WMS", "Inbound/outbound; inventory; LPN scanning; dock assignment", "SAP WM/EWM or standalone"],
        ]
        self._build_table(st, components, s, col_widths=[2.0*inch, 2.6*inch, 1.9*inch])
        st.append(Spacer(1, 12))

        # ── 3. PODISE / APS Design ────────────────────────────────────────────
        st.append(Paragraph("3. PODISE — Production Order Design & Intelligent Scheduling", s["section_heading"]))
        st.append(Paragraph(
            "PODISE solves the fundamental limitation of SAP MRP for solar manufacturing: "
            "it converts sales orders to production orders in under 2 seconds, handles "
            "solar-specific lot-size constraints (laminator batches of 4-12, flash tester 1, "
            "packaging 30), and re-optimizes schedules within 30 seconds of any disruption.",
            s["body"]
        ))
        st.append(Spacer(1, 8))
        self._embed_diagram(st, diagrams.get("podise_flow"), "PODISE Process Flow", s, w=4.5, h=4.0)
        st.append(Spacer(1, 8))

        # APS comparison table
        st.append(Paragraph("APS vs. SAP MRP — Capability Comparison", s["sub_heading"]))
        aps_compare = [
            ["Capability", "SAP MRP", "PODISE/APS"],
            ["Scheduling granularity", "Day-level", "Hour / minute-level"],
            ["Capacity handling", "Infinite (ignores constraints)", "Finite (real constraints respected)"],
            ["Rush order response", "Batch MRP run required (1+ hour)", "< 30 seconds automated"],
            ["Lot-size constraints", "Basic min/max", "Complex multi-level (solar-specific)"],
            ["Technology variants", "Limited BOM handling", "Full PERC/TOPCon/Bifacial/HJT"],
            ["Bottleneck visibility", "None", "Real-time bottleneck identification"],
            ["Re-optimization on breakdown", "Manual replanning", "Automatic on Kafka event"],
            ["Gantt visualization", "None built-in", "Real-time Angular Gantt; drag-drop"],
            ["AI recommendations", "None", "Plain-English rescheduling advice"],
        ]
        self._build_table(st, aps_compare, s, col_widths=[2.4*inch, 2.0*inch, 2.1*inch])
        st.append(Spacer(1, 12))

        # ── 4. Multi-Agent AI System ──────────────────────────────────────────
        st.append(Paragraph("4. Multi-Agent AI System Design", s["section_heading"]))
        st.append(Paragraph(
            "The MES orchestrates 9 specialized AI agents coordinated by a supervisor "
            "agent (LangChain4j @SupervisorAgent pattern). Each agent has a specific domain, "
            "communicates via Kafka, and uses the MCP tool registry to call external services. "
            "The on-premises Ollama + Llama 3.2 ensures manufacturing IP stays within the factory.",
            s["body"]
        ))
        st.append(Spacer(1, 8))
        self._embed_diagram(st, diagrams.get("agent_design"), "Multi-Agent System Design", s, w=6.0, h=4.5)
        st.append(Spacer(1, 8))

        agents_table = [
            ["Agent", "Primary Responsibility", "Key AI Capability"],
            ["Orchestrator Agent", "Receives high-level goals; coordinates all agents; persists workflow state in PostgreSQL", "Goal decomposition; fault-tolerant task sequencing"],
            ["PODISE / APS Agent", "Sales order → production order in <2s; lot splitting; backward/forward scheduling", "Constraint-based scheduling; multi-objective optimization"],
            ["Line Scheduler Agent", "Finite-capacity scheduling per work center; Gantt push via WebSocket", "Real-time re-optimization on breakdown or rush order"],
            ["PDI/PDO Tracking Agent", "Ingests machine data (OPC UA, MQTT, Excel); publishes Kafka events; PDI/PDO records", "AI scrap analysis; cycle-time anomaly detection; NL recommendations"],
            ["Quality Inspection Agent", "AI-AOI + EL image classification; flash test capture; defect coding and disposition", "CNN defect detection >98% accuracy; IEC 61215 compliance"],
            ["Predictive Maint. Agent", "Monitors sensor streams; forecasts machine failure hours ahead; creates PM work orders", "Time-series anomaly detection; MTBF prediction"],
            ["Material Allocation Agent", "Auto-reserves components in SAP; manages shortages; supplier alerts", "Shortage prediction; alternative material suggestion"],
            ["Dispatch Planning Agent", "AI-optimized pallet/truck loading; dock assignment; ALMM COC generation", "Route optimization; fill-rate maximization"],
            ["Reporting Agent", "Shift-end summaries; OEE trends; scrap analysis; plain-English AI narration", "LLM-generated natural language reports for management"],
        ]
        self._build_table(st, agents_table, s, col_widths=[1.8*inch, 2.8*inch, 2.0*inch])
        st.append(Spacer(1, 12))

        # ── 5. Integration Architecture ───────────────────────────────────────
        st.append(Paragraph("5. Integration Architecture", s["section_heading"]))
        self._embed_diagram(st, diagrams.get("integration"), "Integration Architecture Diagram", s, w=6.0, h=3.5)
        st.append(Spacer(1, 8))

        integration_table = [
            ["Integration", "Direction", "Protocol / Method", "Frequency", "Key Data"],
            ["SAP ERP ↔ PODISE", "Bidirectional", "REST API + IDoc", "Real-time / Hourly batch", "Sales orders, prod orders, BOM, routings, confirmations"],
            ["MES ↔ SAP (QM/WM)", "Bidirectional", "REST API / IDoc", "Event-driven", "Quality results, GR/GI, material movements"],
            ["OPC UA Gateway → Kafka", "Unidirectional", "OPC UA subscription", "1-5 seconds", "Machine status, sensor values, alarm events"],
            ["Flash Tester → MES", "Unidirectional", "OPC UA / REST", "Per test cycle", "IV curve, Pmax, Voc, Isc, FF, temperature"],
            ["EL Tester → MES", "Unidirectional", "OPC UA / File", "Per test cycle", "Image classification result, defect type, coordinates"],
            ["MES ↔ WMS", "Bidirectional", "REST API", "Event-driven", "Pick instructions, inventory confirmation, batch locations"],
            ["MES → ALMM Portal", "Unidirectional", "REST API (MNRE)", "On dispatch", "Module serial, test results, COC data"],
            ["Kafka → PostgreSQL", "Unidirectional", "Kafka Consumer", "Continuous", "All MES events (replay-capable audit trail)"],
            ["Kafka → InfluxDB", "Unidirectional", "Kafka Consumer", "Continuous", "Time-series sensor data for OEE/trend analysis"],
        ]
        self._build_table(st, integration_table, s, col_widths=[1.5*inch, 1.0*inch, 1.4*inch, 1.1*inch, 1.6*inch])
        st.append(Spacer(1, 12))

        # ── 6. Data Flow ──────────────────────────────────────────────────────
        st.append(Paragraph("6. End-to-End Data Flow", s["section_heading"]))
        flows = [
            ["Step", "From", "To", "Data", "Storage"],
            ["1", "Machine (Stringer/Laminator)", "OPC UA Gateway", "Raw sensor readings, status, counts", "Edge buffer"],
            ["2", "OPC UA Gateway", "Kafka topic: raw-machine-data", "Timestamped tag values", "Kafka (7-day retention)"],
            ["3", "Kafka", "PDI/PDO Tracking Agent", "Operation log events", "In-memory processing"],
            ["4", "PDI/PDO Agent", "PostgreSQL", "Validated PDI/PDO records, alerts", "Permanent (audit trail)"],
            ["5", "PDI/PDO Agent", "InfluxDB", "Time-series metrics (OEE components)", "90-day hot; S3 archive"],
            ["6", "EL Tester", "Quality Inspection Agent", "Raw EL image (TIFF/PNG)", "GPU processing"],
            ["7", "Quality Inspection Agent", "PostgreSQL + Document Store", "Classification result + image path", "Permanent (linked to serial)"],
            ["8", "Flash Tester", "MES QMS Module", "IV curve data per module serial", "PostgreSQL (ALMM)"],
            ["9", "MES", "SAP ERP", "Production confirmation, actual quantities", "SAP OLTP"],
            ["10", "MES", "ALMM Portal (MNRE)", "Module serial + all test results + COC", "MNRE compliance DB"],
            ["11", "PostgreSQL + InfluxDB", "Analytics Engine", "Aggregated KPIs, trends", "Data warehouse"],
            ["12", "Analytics Engine", "Angular Portal", "OEE gauges, Gantt, shift reports", "Browser (WebSocket)"],
        ]
        self._build_table(st, flows, s, col_widths=[0.4*inch, 1.5*inch, 1.5*inch, 1.7*inch, 1.5*inch])
        st.append(Spacer(1, 12))

        # ── 7. Deployment Architecture ────────────────────────────────────────
        st.append(Paragraph("7. Deployment Architecture", s["section_heading"]))
        st.append(Paragraph(
            "Hybrid deployment model: Core MES, PODISE, and OPC UA integration run on-premise "
            "to ensure low latency (<100ms) for real-time shop-floor operations. Analytics, "
            "document storage, and AI model serving run on-premise GPU server. Cloud is optional "
            "for analytics dashboards and remote monitoring.",
            s["body"]
        ))
        st.append(Spacer(1, 6))
        deploy_table = [
            ["Layer", "Component", "Location", "Hardware Spec"],
            ["Application", "Solar MES Platform", "On-premise DC", "2× 16-core server, 64 GB RAM, 2 TB SSD"],
            ["Application", "PODISE / APS Engine", "On-premise DC", "Shared with MES server"],
            ["AI Inference", "Ollama + Llama 3.2 + EL Classifier", "On-premise GPU server", "NVIDIA A10/RTX 4090, 48 GB VRAM"],
            ["Database", "PostgreSQL (primary)", "On-premise DC", "32-core, 128 GB RAM, 10 TB NVMe RAID-10"],
            ["Database", "InfluxDB (time-series)", "On-premise DC", "16-core, 64 GB RAM, 5 TB SSD"],
            ["Messaging", "Apache Kafka Cluster (3 nodes)", "On-premise DC", "3× 8-core, 32 GB RAM, 2 TB each"],
            ["Edge", "OPC UA Gateway per line", "Shop floor (per line)", "Industrial IPC (Advantech/Siemens), fanless"],
            ["Network", "OT/IT Segregated Network", "Factory", "Firewall DMZ; TLS 1.3; VLAN per line"],
            ["Frontend", "Angular Portal (Web)", "On-premise app server", "Shared; CDN for static assets"],
            ["Display", "OEE Display per Line", "Shop floor (per line)", "55\" industrial display; Raspberry Pi / IPC"],
        ]
        self._build_table(st, deploy_table, s, col_widths=[1.2*inch, 2.0*inch, 1.5*inch, 2.0*inch])
        st.append(Spacer(1, 12))

        # ── 8. Security Architecture ──────────────────────────────────────────
        st.append(Paragraph("8. Security Architecture", s["section_heading"]))
        sec_items = [
            ("Authentication & Authorisation", "OAuth2 / JWT tokens; Role-Based Access Control (RBAC); per-module permissions; session timeout 8 hours"),
            ("Network Security", "OT/IT network segregation; DMZ for MES; TLS 1.3 for all API communication; no direct internet access for OT layer"),
            ("Data Encryption", "Encryption at rest (AES-256) for PostgreSQL and document store; encryption in transit (TLS) for all Kafka, REST, OPC UA traffic"),
            ("Audit Logging", "Immutable audit log for all user actions; retained 3 years minimum; ALMM compliance requirement"),
            ("Backup & Recovery", "Daily automated backup to encrypted off-site storage; RTO ≤ 4 hours; RPO ≤ 1 hour; quarterly DR drill"),
            ("OT Security", "OPC UA authentication (X.509 certificates); machine whitelist; no direct internet from PLC/SCADA layer"),
            ("AI Data Privacy", "On-premises LLM inference; manufacturing IP never sent to cloud APIs; model updates via air-gapped process"),
            ("Vulnerability Management", "Quarterly security assessment; CVE monitoring; patch management SLA (critical: 48h, high: 7 days)"),
        ]
        for title, detail in sec_items:
            st.append(Paragraph(f"<b>{title}:</b> {detail}", s["body"]))
        st.append(Spacer(1, 14))

        st.append(HRFlowable(width="100%", thickness=1, color=BRAND_MID))
        st.append(Spacer(1, 6))
        st.append(Paragraph(
            "This HLD is a living document. Detailed Low-Level Design (LLD) will be produced during Phase 1 (Discovery & Blueprint).",
            s["small"]
        ))
        doc.build(st)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _embed_diagram(self, story, path, label, s, w=5.5, h=3.5):
        if path and os.path.exists(path):
            try:
                story.append(Image(os.path.abspath(path), width=w*inch, height=h*inch))
                story.append(Spacer(1, 4))
            except Exception as exc:
                print(f"   ⚠️  HLD embed {label}: {exc}")
                story.append(Paragraph(f"[{label} — diagram not available]", s["small"]))
        else:
            story.append(Paragraph(f"[{label} — diagram not generated (Kroki unavailable)]", s["small"]))

    def _build_table(self, story, data, s, col_widths):
        rows = []
        for i, row in enumerate(data):
            style = s["table_header"] if i == 0 else s["table_cell"]
            rows.append([Paragraph(str(cell), style) for cell in row])
        tbl = Table(rows, colWidths=col_widths)
        tbl.setStyle(default_table_style())
        story.append(tbl)