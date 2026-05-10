"""
crews/presales_crew.py
-----------------------
CrewAI crew wrapping all existing agents.
Two stages:
  run_analysis()      -> requirements + clarifying questions (fast, ~2min)
  run_full_pipeline() -> calls existing main.run_presales() after crew enrichment
"""
import json, os, sys
from typing import Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from llm_factory import get_llm
from json_utils import parse_json


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool("load_knowledge_base")
def load_knowledge_base(industry: str) -> str:
    """Load the industry knowledge base. Falls back to solar/general if not found."""
    base = os.path.dirname(os.path.dirname(__file__))
    slug = industry.strip().lower().replace(" ", "_")
    paths = [
        os.path.join(base, "data", slug, "knowledge.txt"),
        os.path.join(base, "data", f"{slug}_knowledge.txt"),
        os.path.join(base, "data", "industry_knowledge.txt"),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                content = f.read(10000)
            return f"[Loaded: {p}]\n\n{content}"
    return "Knowledge base not found. Use general manufacturing best practices."


@tool("list_industries")
def list_industries() -> str:
    """List all industries that have a dedicated knowledge base."""
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    found = ["solar (default)"]
    try:
        for item in os.listdir(base):
            fp = os.path.join(base, item)
            if os.path.isdir(fp) and os.path.exists(os.path.join(fp, "knowledge.txt")):
                found.append(item.replace("_", " ").title())
    except Exception:
        pass
    return ", ".join(found)


@tool("generate_questions")
def generate_questions(requirements_json: str) -> str:
    """Generate 4-6 clarifying questions to fill gaps in the requirements."""
    from langchain_core.messages import HumanMessage
    llm = get_llm(temperature=0.3)
    prompt = f"""You are a senior manufacturing pre-sales consultant.
Given these extracted requirements, identify gaps and generate 4-6 precise clarifying questions.
Focus on: production scale, existing systems, budget/timeline, compliance (ALMM/GMP etc.), integration needs.

Requirements: {requirements_json}

Return ONLY a JSON array of question strings. No explanation."""
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        qs = parse_json(resp.content, fallback=[])
        if isinstance(qs, list) and len(qs) >= 2:
            return json.dumps(qs)
    except Exception:
        pass
    return json.dumps([
        "What is your current annual production capacity (MW/tons/units)?",
        "Which ERP/SCADA/MES systems are currently in use, and which version?",
        "What is your target go-live date and total budget envelope (USD)?",
        "Are there specific regulatory/compliance requirements (ALMM, GMP, ISO, etc.)?",
        "How many production lines and distinct machine types need integration?",
        "How many operators and supervisors will use the system daily?",
    ])


# ─── Agents ───────────────────────────────────────────────────────────────────

def _llm():
    return get_llm(temperature=0.2)


def make_classifier():
    return Agent(
        role="Industry & Domain Classifier",
        goal="Identify the manufacturing industry and select the right knowledge base.",
        backstory=(
            "Expert in 20+ manufacturing domains: solar PV, steel, automotive, logistics, "
            "pharma, food & beverage, electronics. Instantly recognises industry-specific "
            "terminology and compliance contexts."
        ),
        tools=[list_industries, load_knowledge_base],
        llm=_llm(), verbose=True, allow_delegation=False,
    )


def make_requirements_analyst():
    return Agent(
        role="Senior Requirements Analyst",
        goal="Extract complete structured requirements and identify all gaps.",
        backstory=(
            "15 years in manufacturing pre-sales. Knows exactly what information is "
            "needed for a credible proposal. Extracts maximum value from any customer input."
        ),
        tools=[generate_questions],
        llm=_llm(), verbose=True, allow_delegation=False,
    )


def make_domain_analyst():
    return Agent(
        role="Domain Knowledge Analyst",
        goal="Retrieve and synthesise the most relevant manufacturing best practices.",
        backstory=(
            "Deep knowledge of MES, APS, WMS, SCADA, ERP across all manufacturing industries. "
            "Provides specific benchmarks, ROI data, and compliance requirements."
        ),
        tools=[load_knowledge_base],
        llm=_llm(), verbose=True, allow_delegation=False,
    )


def make_reviewer():
    return Agent(
        role="Pre-Sales Quality Reviewer",
        goal="Review requirements for completeness and suggest improvements.",
        backstory=(
            "VP of Pre-Sales who has reviewed 500+ proposals. Identifies missing information "
            "and ensures every proposal is technically sound and commercially competitive."
        ),
        tools=[generate_questions],
        llm=_llm(), verbose=True, allow_delegation=False,
    )


# ─── Tasks ────────────────────────────────────────────────────────────────────

def task_classify(agent, query: str) -> Task:
    return Task(
        description=f"""
Analyse this customer query:
{query}

1. Identify the industry (Solar, Steel, Automotive, Logistics, Pharma, etc.)
2. Identify the sub-domain (e.g. solar module assembly, hot rolling, cold chain)
3. List applicable compliance/regulatory requirements
4. Load the appropriate knowledge base using the tool
5. Return JSON:
{{
  "industry": "...",
  "sub_domain": "...",
  "regulatory_context": ["..."],
  "knowledge_base_summary": "3-4 sentence summary of key domain facts"
}}""",
        expected_output="JSON with industry classification and knowledge base summary",
        agent=agent,
    )


def task_extract(agent, query: str) -> Task:
    return Task(
        description=f"""
Extract structured requirements from this customer query:
{query}

Step 1: Extract initial requirements with these exact JSON keys:
  industry, product, production_capacity, lines (int), machine_types (int),
  erp (string or null), current_systems (list), pain_points (list),
  requirements (list), customization (low/medium/high), extra_notes

Step 2: Call the generate_questions tool with the requirements JSON to get clarifying questions.

Step 3: Identify confidence score (0-100) and any critical gaps.

Return JSON:
{{
  "requirements": {{...}},
  "clarifying_questions": ["..."],
  "confidence_score": 75,
  "gaps": ["list of missing information"]
}}""",
        expected_output="Requirements JSON with clarifying questions and gaps",
        agent=agent,
    )


def task_domain_knowledge(agent, industry: str) -> Task:
    return Task(
        description=f"""
Load the knowledge base for {industry} manufacturing.
Synthesise the most important domain knowledge covering:
1. Key MES/software modules recommended for this industry
2. Manufacturing process steps (specific to this industry)
3. Integration patterns and protocols
4. Compliance requirements
5. ROI benchmarks (payback periods, OEE improvements, cost reductions)
6. Common pain points and proven solutions

Return a detailed plain-text summary (minimum 500 words).""",
        expected_output="Comprehensive domain knowledge summary",
        agent=agent,
    )


def task_review(agent) -> Task:
    return Task(
        description="""
Review the requirements and domain knowledge gathered in previous tasks.
Assess:
1. Requirements completeness (score 1-10, what is missing?)
2. Are there additional questions needed?
3. What are the 5 strongest selling points for this customer?
4. What are the top 3 likely objections and how to handle them?

Return JSON:
{
  "completeness_score": 8,
  "missing_items": ["..."],
  "additional_questions": ["..."],
  "selling_points": ["..."],
  "objections": [{"objection": "...", "response": "..."}]
}""",
        expected_output="Quality review JSON with selling strategy",
        agent=agent,
    )


# ─── Crew Class ───────────────────────────────────────────────────────────────

class PresalesCrew:
    def __init__(self, customer_query: str, answers: Optional[dict] = None):
        self.query = customer_query
        self.answers = answers or {}
        # Build enriched query with user answers
        if self.answers:
            qa = "\n".join(f"Q: {q}\nA: {a}" for q, a in self.answers.items())
            self.enriched = f"{customer_query}\n\nCustomer clarifications:\n{qa}"
        else:
            self.enriched = customer_query

    def run_analysis(self) -> dict:
        """Stage 1: Extract requirements + generate questions (fast, ~2-3 min)."""
        classifier = make_classifier()
        analyst    = make_requirements_analyst()

        crew = Crew(
            agents=[classifier, analyst],
            tasks=[task_classify(classifier, self.enriched),
                   task_extract(analyst, self.enriched)],
            process=Process.sequential,
            verbose=True,
        )
        try:
            result = crew.kickoff()
            raw = str(result.raw) if hasattr(result, "raw") else str(result)
            parsed = parse_json(raw, fallback={})
            return {
                "requirements": parsed.get("requirements", {}),
                "clarifying_questions": parsed.get("clarifying_questions", [
                    "What is your current annual production capacity?",
                    "Which ERP system are you using (SAP, Oracle, etc.)?",
                    "What is your target go-live timeline and budget?",
                    "Are there regulatory compliance requirements?",
                    "How many operators will use the system daily?",
                ]),
                "confidence_score": parsed.get("confidence_score", 70),
                "gaps": parsed.get("gaps", []),
            }
        except Exception as e:
            return {
                "requirements": {},
                "clarifying_questions": [
                    "What is your current annual production capacity?",
                    "Which ERP system are you using (SAP, Oracle, etc.)?",
                    "What is your target go-live timeline and budget?",
                    "Are there regulatory compliance requirements?",
                    "How many operators will use the system daily?",
                ],
                "confidence_score": 40,
                "gaps": [str(e)],
            }

    def run_domain_enrichment(self, industry: str) -> dict:
        """Stage 2: Get deep domain knowledge for document enrichment."""
        domain_analyst = make_domain_analyst()
        reviewer       = make_reviewer()
        crew = Crew(
            agents=[domain_analyst, reviewer],
            tasks=[task_domain_knowledge(domain_analyst, industry),
                   task_review(reviewer)],
            process=Process.sequential,
            verbose=True,
        )
        try:
            result = crew.kickoff()
            raw = str(result.raw) if hasattr(result, "raw") else str(result)
            review_data = parse_json(raw, fallback={})
            return {
                "domain_knowledge": raw,
                "review": review_data,
            }
        except Exception as e:
            return {"domain_knowledge": "", "review": {}, "error": str(e)}
