"""
agents/requirement_debate.py
-----------------------------
Two-agent LangGraph debate that refines raw customer input into a
validated, structured requirements dict.

  extract_initial_requirements
          │
          ▼
    client_advocate      (adds business / ROI / training needs)
          │
          ▼
    technical_expert     (adds protocols, scalability, security)
          │
          ▼
         END  →  state["final_requirements"]
"""
import operator
import os
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from json_utils import parse_json
from llm_factory import get_llm


# ── State ─────────────────────────────────────────────────────────────────────

class DebateState(TypedDict):
    customer_query: str
    requirements: dict
    client_advocate_view: str
    technical_expert_view: str
    final_requirements: dict
    messages: Annotated[list, operator.add]


# ── Node functions ─────────────────────────────────────────────────────────────

def extract_initial_requirements(state: DebateState) -> DebateState:
    """Convert free-text customer query → structured JSON."""
    llm = get_llm(temperature=0)
    prompt = f"""
You are a manufacturing pre-sales expert.
Extract structured requirements from the customer input below.

Return ONLY a valid JSON object with exactly these keys:
{{
  "industry": "e.g. Solar, Steel, Automotive",
  "product": "what they manufacture",
  "production_capacity": "number + unit",
  "lines": <integer number of production lines>,
  "machine_types": <integer number of distinct machine types>,
  "erp": "<ERP system name or null>",
  "current_systems": ["list of existing systems"],
  "pain_points": ["list of problems"],
  "requirements": ["list of functional needs"],
  "customization": "low | medium | high",
  "extra_notes": "anything else"
}}

Customer input:
{state["customer_query"]}
"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    parsed = parse_json(
        resp.content,
        fallback={
            "industry": "Manufacturing",
            "product": "Unknown",
            "production_capacity": "N/A",
            "lines": 2,
            "machine_types": 5,
            "erp": None,
            "current_systems": [],
            "pain_points": [],
            "requirements": [],
            "customization": "medium",
            "extra_notes": "",
        },
    )
    state["requirements"] = parsed
    return state


def client_advocate(state: DebateState) -> DebateState:
    """Add business/ROI/training/change-management gaps."""
    import json
    llm = get_llm(temperature=0.3)
    prompt = f"""
You are a client advocate in a manufacturing pre-sales review.
Review the original customer request and the extracted requirements.
Add any missing BUSINESS needs: ROI expectations, training, change management,
post-go-live support, budget constraints, timeline preferences.

Return ONLY a valid JSON object with exactly these two keys:
{{
  "critique": "short explanation of what you added",
  "revised_requirements": {{ <same structure as the input requirements, updated> }}
}}

Original query:
{state["customer_query"]}

Current requirements:
{json.dumps(state["requirements"], indent=2)}
"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    data = parse_json(resp.content, fallback={})
    state["client_advocate_view"] = data.get("critique", "")
    revised = data.get("revised_requirements", {})
    if revised and isinstance(revised, dict):
        state["requirements"].update(revised)
    return state


def technical_expert(state: DebateState) -> DebateState:
    """Add technical gaps: protocols, scalability, security, integration detail."""
    import json
    llm = get_llm(temperature=0.3)
    prompt = f"""
You are a manufacturing technology architect in a pre-sales review.
Validate the current requirements for technical accuracy and completeness.
Add missing TECHNICAL details: integration protocols (OPC UA, Modbus, REST),
scalability, security, network architecture, disaster recovery.

Return ONLY a valid JSON object with exactly these two keys:
{{
  "critique": "short explanation of what you added",
  "final_requirements": {{ <complete, merged requirements object> }}
}}

Original query:
{state["customer_query"]}

Current requirements (after client advocate):
{json.dumps(state["requirements"], indent=2)}
"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    data = parse_json(resp.content, fallback={})
    state["technical_expert_view"] = data.get("critique", "")
    final = data.get("final_requirements", {})
    state["final_requirements"] = final if final else state["requirements"]
    return state


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_debate_graph():
    wf = StateGraph(DebateState)
    wf.add_node("extract", extract_initial_requirements)
    wf.add_node("client_advocate", client_advocate)
    wf.add_node("technical_expert", technical_expert)
    wf.set_entry_point("extract")
    wf.add_edge("extract", "client_advocate")
    wf.add_edge("client_advocate", "technical_expert")
    wf.add_edge("technical_expert", END)
    return wf.compile()
