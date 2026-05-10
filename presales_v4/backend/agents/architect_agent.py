"""
agents/architect_agent.py
--------------------------
Generates architecture narrative using LLM.
Enhanced with AI-native MES, PODISE, Kafka, MCP, agentic-AI knowledge.
"""
import json
from langchain_core.messages import HumanMessage
from llm_factory import get_llm

class ArchitectAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, state: dict) -> dict:
        req = json.dumps(state.get("requirements", {}), indent=2)
        domain = state.get("domain_knowledge", "")

        prompt = f"""
You are a senior manufacturing systems architect for solar panel factories.

Design a **detailed**, **professional** system architecture.

Structure your response with these numbered sections:

1. **Architecture Overview** (2‑3 sentences)
2. **System Components** – bullet list:
   - SAP ERP (SD/PP modules)
   - Solar MES Platform (Production Order Mgmt, SFDC, QMS, Equipment Integration, OEE)
   - PODISE Engine (real‑time sales‑order‑to‑production‑order conversion, lot splitting, backward/forward scheduling)
   - Line Scheduler (batch‑aware, finite‑capacity, Gantt real‑time)
   - Production Tracking Agent PDI/PDO (OPC‑UA, MQTT, TCP/IP, Excel ingestion → Kafka → PostgreSQL)
   - Quality Inspection Agent (AI‑AOI, EL image classification, flash‑test capture)
   - Predictive Maintenance Agent (sensor streams → failure forecast)
   - OPC‑UA Gateway, Kafka Event Bus, IoT Pipeline, Data Lake, Analytics Engine, Angular Portal
3. **Integration Points** – protocol, direction, frequency for each pair
4. **Data Flow** – end‑to‑end: machine → OPC‑UA → Kafka → PostgreSQL → Analytics → Dashboard
5. **Deployment Model** – hybrid (on‑premise MES + cloud Data Lake/Analytics)

Use clear technical English. No markdown headers.

Requirements:
{req}

Domain Knowledge:
{domain}
"""
        resp = self.llm.invoke([HumanMessage(content=prompt)])
        state["architecture"] = resp.content.strip()
        return state