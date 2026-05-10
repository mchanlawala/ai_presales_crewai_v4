"""
agents/diagram_agent.py
------------------------
Enhanced PlantUML component diagram generator.
Includes PODISE, Kafka, AI Agents, OPC‑UA, and MCP layer.
"""
import re
from langchain_core.messages import HumanMessage
from llm_factory import get_llm

FALLBACK_DIAGRAM = """@startuml
skinparam componentStyle rectangle
skinparam backgroundColor #FAFAFA
skinparam component { BackgroundColor #EAF2FB BorderColor #2E6DA4 FontColor #1A2E44 }

component "SAP ERP (SD/PP)" as erp
component "PODISE Engine" as podise
component "Line Scheduler" as ls
component "Solar MES Platform" as mes {
    component "Production Order Mgmt" as pom
    component "Shop Floor Data (SFDC)" as sfdc
    component "Quality Mgmt (QMS)" as qms
    component "Equipment Integration" as ei
}
component "Kafka Event Bus" as kafka
component "OPC UA Gateway" as opcua
component "SCADA / PLC Layer" as scada
component "PDI/PDO Tracking Agent" as pdi
component "Quality Inspection Agent" as qa
component "Predictive Maint. Agent" as pma
component "PostgreSQL" as pg
component "Data Lake / Analytics" as analytics
component "Angular Portal (UI)" as ui

erp --> podise : Sales Orders (REST/IDoc)
podise --> kafka : Scheduled Orders
kafka --> ls : Production Orders
ls --> mes : Line Schedule (batches)
mes --> opcua : Machine Commands
opcua --> scada : Control Signals
scada --> opcua : Sensor Data
opcua --> kafka : Real-time Events
kafka --> pdi : Raw Operation Logs
pdi --> pg : PDI/PDO Records
kafka --> qa : EL Images / Test Results
qa --> pg : Quality Records
kafka --> pma : Sensor Streams
pma --> mes : Maintenance Alerts
pg --> analytics : Aggregated KPIs
analytics --> ui : Dashboards & Gantt
mes --> erp : Production Confirmations
@enduml"""

class DiagramAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, state: dict) -> str:
        arch_text = state.get("architecture", "")
        if not arch_text.strip():
            return FALLBACK_DIAGRAM
        raw = self._ask_llm(arch_text)
        code = self._clean(raw)
        if self._is_valid(code):
            return code
        print("⚠️  DiagramAgent: using enhanced fallback diagram.")
        return FALLBACK_DIAGRAM

    def _ask_llm(self, arch_text: str) -> str:
        prompt = f"""
Convert this architecture into a valid PlantUML COMPONENT DIAGRAM.
RULES:
- First line: @startuml (exactly). Last line: @enduml.
- Declare: component "Name" as alias
- Draw: alias1 --> alias2 : label
- Include: SAP ERP, PODISE, Line Scheduler, Solar MES, Kafka, OPC UA Gateway,
  SCADA, PDI/PDO Tracking Agent, Quality Agent, Predictive Maintenance Agent,
  PostgreSQL, Data Lake, Angular Portal.
- No markdown fences. No explanation.

Architecture:
{arch_text}
"""
        try:
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            return resp.content.strip()
        except Exception as exc:
            print(f"⚠️  Diagram LLM failed: {exc}")
            return ""

    def _clean(self, text: str) -> str:
        text = re.sub(r"```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```", "", text).strip()
        m = re.search(r"(@startuml.*?@enduml)", text, re.DOTALL)
        return m.group(1).strip() if m else text

    def _is_valid(self, code: str) -> bool:
        lines = [l.strip() for l in code.splitlines() if l.strip()]
        if not lines: return False
        if not lines[0].startswith("@startuml"): return False
        if not lines[-1].startswith("@enduml"): return False
        return "component" in "\n".join(lines[1:-1]) or "-->" in "\n".join(lines[1:-1])