"""
agents/infrastructure_deployment_agent.py
------------------------------------------
Document 8 of 12: Infrastructure & Deployment Architecture
Covers: server specs, network topology, OT/IT segregation,
backup/DR, hardware bill of materials, cloud vs on-premise decisions.
Result → state["infrastructure_pdf_path"]
"""
import datetime, os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID, BRAND_LIGHT,
    get_styles, default_table_style, strip_markdown, nl2br,
)
from diagram_utils import render_plantuml

_DEPLOYMENT_DIAGRAM = """@startuml
skinparam backgroundColor #FAFAFA
skinparam defaultFontName Arial

package "Enterprise Zone (IT Network)" {
  node "SAP ERP Server\\n(Existing)" as sap
  node "MES Application Server\\n(16-core, 64GB RAM)" as mes_app
  node "MES DB Server\\n(PostgreSQL, 128GB)" as mes_db
  node "InfluxDB Time-Series\\n(16-core, 64GB)" as influx
  node "Kafka Cluster\\n(3 nodes, 32GB each)" as kafka
  node "AI Inference Server\\n(GPU: NVIDIA A10)" as ai_srv
  node "Angular Web Server\\n(4-core, 16GB)" as web
}

package "DMZ (Firewall Protected)" {
  node "OPC UA Aggregator\\n(Kepware / Ignition)" as opcua_agg
  node "API Gateway\\n(Rate limit, Auth)" as apigw
}

package "Shop Floor (OT Network)" {
  node "Edge Gateway Line 1\\n(Industrial IPC)" as edge1
  node "Edge Gateway Line 2\\n(Industrial IPC)" as edge2
  node "Edge Gateway Line 3\\n(Industrial IPC)" as edge3
  node "Edge Gateway Line 4\\n(Industrial IPC)" as edge4
}

package "Field Layer (L0/L1)" {
  node "Stringer PLC\\n(Siemens S7)" as plc_str
  node "Laminator PLC\\n(Allen Bradley)" as plc_lam
  node "Flash Tester\\n(OPC UA native)" as flash
  node "EL Tester\\n(TCP/File)" as el
}

sap <--> mes_app : REST/IDoc
mes_app <--> mes_db : JDBC
mes_app <--> kafka : Kafka protocol
kafka <--> influx : Consumer
mes_app <--> ai_srv : REST (image classification)
web <--> mes_app : REST/WebSocket
opcua_agg <--> apigw : OPC UA
apigw <--> mes_app : REST
edge1 --> opcua_agg : OPC UA (TLS)
edge2 --> opcua_agg : OPC UA (TLS)
edge3 --> opcua_agg : OPC UA (TLS)
edge4 --> opcua_agg : OPC UA (TLS)
plc_str --> edge1 : OPC UA
plc_lam --> edge1 : OPC UA
flash --> edge1 : OPC UA native
el --> edge1 : TCP socket / File
@enduml"""

_NETWORK_DIAGRAM = """@startuml
skinparam backgroundColor #FAFAFA
title Network Segmentation — Solar MES

node "Internet / Cloud\\n(Analytics, Remote Support)" as internet
node "Firewall 1\\n(Edge Firewall)" as fw1
node "Corporate LAN\\n(IT Network, VLAN 10)" as lan
node "DMZ\\n(VLAN 20)" as dmz
node "Firewall 2\\n(OT Firewall)" as fw2
node "OT Network\\n(VLAN 30, per-line VLANs)" as ot
node "Field Devices\\n(L0/L1 PLCs, Instruments)" as field

internet --> fw1 : HTTPS only
fw1 --> lan : Stateful inspection
fw1 --> dmz : DMZ rules
lan --> dmz : API calls (port 443)
dmz --> fw2 : OPC UA (port 4840, TLS)
fw2 --> ot : Industrial protocols
ot --> field : Profibus / OPC UA
@enduml"""


class InfrastructureDeploymentAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/infrastructure_deployment.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        diagrams = self._render_diagrams()
        self._build_pdf(state, diagrams, output_path)
        state["infrastructure_pdf_path"] = output_path
        return state

    def _render_diagrams(self) -> dict:
        paths = {}
        for key, code, fname in [
            ("deploy", _DEPLOYMENT_DIAGRAM, "infra_deployment.png"),
            ("network", _NETWORK_DIAGRAM,   "infra_network.png"),
        ]:
            try:
                paths[key] = render_plantuml(code, filename=fname)
                print(f"   ✓ {fname}")
            except Exception as e:
                print(f"   ⚠️  {fname}: {e}")
                paths[key] = None
        return paths

    def _build_pdf(self, state: dict, diagrams: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []
        req = state.get("requirements", {})
        lines = int(req.get("lines", 4))
        machines = int(req.get("machine_types", 20))

        # ── Banner ────────────────────────────────────────────────────────────
        banner = Table([[Paragraph(
            "Infrastructure & Deployment Architecture<br/>"
            "<font size=13>Hardware, Network, Security & DR Design</font>",
            s["cover_title"]
        )]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
            ("TOPPADDING",(0,0),(-1,-1),20),
            ("BOTTOMPADDING",(0,0),(-1,-1),20),
            ("LEFTPADDING",(0,0),(-1,-1),18),
        ]))
        st += [banner, Spacer(1,6),
               Paragraph(f"{req.get('industry','Solar')} Manufacturing MES — Infrastructure Blueprint | "
                         f"{datetime.date.today().strftime('%d %B %Y')}", s["body"]),
               HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT), Spacer(1,12)]

        # ── 1. Deployment Overview ────────────────────────────────────────────
        st.append(Paragraph("1. Deployment Model Overview", s["section_heading"]))
        st.append(Paragraph(
            "Hybrid deployment: Core MES, PODISE, OPC UA integration, and all real-time "
            "processing run on-premise for latency <100ms. AI inference also runs on-premise "
            "via GPU server (data sovereignty — no manufacturing IP leaves the factory). "
            "Cloud is optional for remote monitoring dashboards only.",
            s["body"]))
        st.append(Spacer(1,8))
        model_data = [
            ["Layer", "Component", "Location", "Rationale"],
            ["Application","Solar MES + PODISE","On-premise","<100ms latency for shop floor operations"],
            ["AI Inference","Ollama + Llama 3.2 + EL Classifier","On-premise GPU","Data sovereignty; no IP to cloud"],
            ["Database","PostgreSQL (primary)","On-premise","ACID compliance; audit trail permanence"],
            ["Time-Series","InfluxDB","On-premise","Local OEE metrics; high-write throughput"],
            ["Messaging","Kafka (3-node cluster)","On-premise","Event replay; zero data loss"],
            ["Edge","OPC UA Gateway per line","Shop floor","Sub-second machine data; offline buffering"],
            ["Frontend","Angular Web Server","On-premise","Served on corporate LAN; WebSocket real-time"],
            ["Analytics (optional)","BI / Reporting","Cloud or on-premise","Long-term trend analysis; management access"],
        ]
        self._tbl(st, model_data, s, [1.3*inch,1.9*inch,1.4*inch,2.0*inch])

        # ── 2. Deployment Diagram ─────────────────────────────────────────────
        st.append(Spacer(1,10))
        st.append(Paragraph("2. System Deployment Diagram", s["section_heading"]))
        self._embed(st, diagrams.get("deploy"), s, w=6.5, h=4.5)

        # ── 3. Server Specifications ──────────────────────────────────────────
        st.append(Paragraph("3. Server Bill of Materials", s["section_heading"]))
        server_data = [
            ["Server","Purpose","CPU","RAM","Storage","Qty","Est. Cost"],
            ["MES App Server","Solar MES + PODISE + Kafka consumers","16-core (Intel Xeon / AMD EPYC)","64 GB ECC","2 TB NVMe SSD (RAID-1)","2 (HA pair)","$8,000–$12,000 each"],
            ["DB Server (PostgreSQL)","Audit trail, genealogy, order history","32-core","128 GB ECC","10 TB NVMe RAID-10","1 primary + 1 replica","$15,000–$20,000 each"],
            ["InfluxDB Server","Time-series OEE, sensor metrics","16-core","64 GB ECC","5 TB SSD (RAID-5)","1","$8,000–$12,000"],
            ["Kafka Broker","3-node cluster for event streaming","8-core each","32 GB each","2 TB SSD each","3","$5,000–$7,000 each"],
            ["AI GPU Server","EL image classification, Ollama LLM","16-core CPU","128 GB RAM","2 TB NVMe","1","$20,000–$35,000"],
            ["Web/API Server","Angular frontend, API gateway","8-core","32 GB","1 TB SSD","1 (+ HA)","$4,000–$6,000"],
            ["Edge IoT Gateway","OPC UA per production line (industrial IPC)","4-core (Atom/i5)","16 GB","256 GB SSD (fanless)","1 per line","$2,000–$4,000 each"],
        ]
        self._tbl(st, server_data, s, [1.4*inch,1.6*inch,1.1*inch,0.7*inch,1.2*inch,0.5*inch,1.1*inch])

        # ── 4. Hardware Summary ───────────────────────────────────────────────
        st.append(Spacer(1,8))
        st.append(Paragraph("4. Hardware Cost Estimate Summary", s["section_heading"]))
        edge_cost = lines * 3000
        total_hw_low = 80000 + edge_cost
        total_hw_high = 150000 + edge_cost
        hw_summary = [
            ["Category","Qty","Estimated Cost (USD)"],
            ["MES Application Servers (HA pair)","2",f"$16,000–$24,000"],
            ["Database Server (primary + replica)","2",f"$30,000–$40,000"],
            ["InfluxDB Server","1","$8,000–$12,000"],
            ["Kafka Cluster (3 nodes)","3","$15,000–$21,000"],
            ["AI/GPU Inference Server","1","$20,000–$35,000"],
            ["Web/API Server","1","$4,000–$6,000"],
            [f"Edge IoT Gateways ({lines} lines)",str(lines),f"${edge_cost:,}–${edge_cost*2:,}"],
            ["OEE Display Screens (55\")","1 per line",f"${lines*600}–${lines*1000}"],
            ["OPC UA License (Kepware/Ignition)","1","$10,000–$25,000"],
            ["Networking (switches, firewall, cables)","—","$15,000–$25,000"],
            ["TOTAL HARDWARE ESTIMATE","—",f"${total_hw_low:,}–${total_hw_high:,}"],
        ]
        self._tbl(st, hw_summary, s, [2.8*inch,1.2*inch,2.6*inch])

        # ── 5. Network Architecture ───────────────────────────────────────────
        st.append(Spacer(1,10))
        st.append(Paragraph("5. Network Architecture", s["section_heading"]))
        st.append(Paragraph(
            "Strict OT/IT segregation is mandatory for security. Three network zones with "
            "stateful firewalls between each zone prevent lateral movement from IT to shop floor.",
            s["body"]))
        st.append(Spacer(1,6))
        self._embed(st, diagrams.get("network"), s, w=5.5, h=3.0)
        st.append(Spacer(1,6))
        net_data = [
            ["Zone","VLAN","Devices","Protocol","Firewall Rules"],
            ["IT / Corporate LAN","VLAN 10","SAP, MES servers, DB, Kafka, Web server","TCP/IP, HTTPS","Outbound to DMZ port 443 only; no direct OT access"],
            ["DMZ","VLAN 20","OPC UA aggregator, API gateway","OPC UA (4840), HTTPS","IT→DMZ: port 443; DMZ→OT: port 4840 TLS only"],
            ["OT Network","VLAN 30+","Edge gateways, SCADA, HMIs","OPC UA, Modbus TCP","No inbound from IT; DMZ can pull on OPC UA subscription"],
            ["Field (L0/L1)","Isolated","PLCs, instruments, vision cameras","Profibus, Ethernet/IP, OPC UA","OT network only; no internet; air-gapped from IT"],
        ]
        self._tbl(st, net_data, s, [0.8*inch,0.8*inch,1.6*inch,1.2*inch,2.2*inch])

        # ── 6. Security Architecture ──────────────────────────────────────────
        st.append(Spacer(1,10))
        st.append(Paragraph("6. Security Architecture", s["section_heading"]))
        sec_data = [
            ["Security Layer","Requirement","Implementation"],
            ["Authentication","MES user login; API access control","OAuth2 / JWT; LDAP/AD integration; MFA for admins"],
            ["Authorisation","Role-based access per module","RBAC: Operator / Supervisor / Planner / Admin / Read-only"],
            ["Data in Transit","All API, Kafka, OPC UA encrypted","TLS 1.3 mandatory; OPC UA with X.509 certificates"],
            ["Data at Rest","PostgreSQL, InfluxDB, document store","AES-256 encryption; encrypted filesystem"],
            ["Audit Log","Immutable action log (ALMM requirement)","Append-only audit table; 3-year retention; tamper-evident"],
            ["OT Security","Machine whitelist; no direct internet","OPC UA authentication; MAC address filtering on OT VLAN"],
            ["Vulnerability Mgmt","Patch management; CVE monitoring","Critical patch SLA: 48 hours; quarterly security assessment"],
            ["Backup","Automated daily backup; off-site copy","PostgreSQL pg_dump + InfluxDB backup to encrypted NAS; weekly offsite"],
        ]
        self._tbl(st, sec_data, s, [1.5*inch,1.8*inch,3.3*inch])

        # ── 7. DR / HA ────────────────────────────────────────────────────────
        st.append(Spacer(1,10))
        st.append(Paragraph("7. High Availability & Disaster Recovery", s["section_heading"]))
        dr_data = [
            ["Requirement","Target","Implementation"],
            ["RTO (Recovery Time Objective)","≤ 4 hours","Hot standby MES app server; PostgreSQL streaming replication"],
            ["RPO (Recovery Point Objective)","≤ 1 hour","Kafka replication (3 replicas); PostgreSQL WAL archiving every 15 min"],
            ["MES Application HA","99.5% uptime","Active-passive HA; health check failover in <60 seconds"],
            ["PostgreSQL HA","99.9% DB uptime","Primary + replica; Patroni for auto-failover"],
            ["Kafka HA","Zero message loss","3-node cluster; replication factor 3; min-ISR 2"],
            ["Edge Gateway","Local buffering 4 hours","Edge stores PDI/PDO locally on connectivity loss; sync on reconnect"],
            ["Backup Frequency","Daily full + 15-min WAL","pg_basebackup (daily); continuous WAL archiving; InfluxDB backup daily"],
            ["DR Drill","Quarterly test","Full failover simulation; RTO/RPO measurement; results documented"],
        ]
        self._tbl(st, dr_data, s, [2.2*inch,1.3*inch,3.1*inch])

        # ── 8. Monitoring ─────────────────────────────────────────────────────
        st.append(Spacer(1,10))
        st.append(Paragraph("8. Infrastructure Monitoring", s["section_heading"]))
        mon_items = [
            ("Application Monitoring", "Prometheus + Grafana: MES API response time, Kafka consumer lag, PostgreSQL query performance, InfluxDB write throughput"),
            ("OT Monitoring", "Edge gateway health: connectivity status per machine, OPC UA subscription latency, buffered data queue depth"),
            ("System Monitoring", "CPU, RAM, disk I/O per server; auto-alert on >80% threshold; PagerDuty / SMS escalation"),
            ("Business Monitoring", "OEE dashboard (Angular): real-time per line/machine; shift summary auto-generated by Reporting Agent"),
            ("Log Management", "Centralized logging (ELK stack or Loki); 90-day hot retention; 1-year archive; ALMM audit trail immutable"),
        ]
        for title, detail in mon_items:
            st.append(Paragraph(f"<b>{title}:</b> {detail}", s["body"]))

        doc.build(st)

    def _tbl(self, story, data, s, widths):
        rows = [[Paragraph(str(c), s["table_header"] if i==0 else s["table_cell"])
                 for c in row] for i, row in enumerate(data)]
        tbl = Table(rows, colWidths=widths)
        tbl.setStyle(default_table_style())
        story.append(tbl)

    def _embed(self, story, path, s, w=5.5, h=3.5):
        if path and os.path.exists(path):
            try:
                story.append(Image(os.path.abspath(path), width=w*inch, height=h*inch))
                story.append(Spacer(1,6))
            except Exception as e:
                story.append(Paragraph(f"[Diagram not embedded: {e}]", s["small"]))
        else:
            story.append(Paragraph("[Diagram not available — Kroki API required]", s["small"]))