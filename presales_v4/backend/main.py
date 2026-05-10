"""
main.py
-------
AI Pre-Sales Consultant – Orchestration Pipeline (v3.0)
Now generates 16 documents covering the full pre-sales package.
Includes: BRD, HLD, Proposal, Process Flow, PoC Plan, Commercial, Risk,
Implementation Roadmap, Infrastructure Deployment, ROI Business Case, and more.
"""
import os
import sys
import zipfile
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from agents.requirement_debate          import build_debate_graph
from agents.knowledge_agent             import KnowledgeAgent
from agents.architect_agent             import ArchitectAgent
from agents.diagram_agent               import DiagramAgent
from agents.estimator_agent             import EstimatorAgent
from agents.process_flow_agent          import ProcessFlowAgent
from agents.discovery_report_agent      import DiscoveryReportAgent
from agents.risk_agent                  import RiskAgent
from agents.proposal_agent              import ProposalAgent
from agents.solar_process_sequence_agent import SolarProcessSequenceAgent
from agents.high_level_design_agent     import HighLevelDesignAgent
from agents.digital_vision_agent        import DigitalVisionAgent
from agents.process_flow_document_agent  import ProcessFlowDocumentAgent
from agents.poc_plan_agent              import PoCPlanAgent
from agents.commercial_proposal_agent   import CommercialProposalAgent
from agents.implementation_roadmap_agent import ImplementationRoadmapAgent
from agents.infrastructure_deployment_agent import InfrastructureDeploymentAgent
from agents.roi_business_case_agent     import ROIBusinessCaseAgent
from diagram_utils                      import render_plantuml


DEFAULT_QUERY = """
We are a solar panel manufacturer producing 300 MW annually.
We use SAP ERP and want to implement MES for:
  - Production tracking and scheduling
  - Quality traceability (batch genealogy from wafer to module)
  - OPC UA machine integration (20 machine types across 4 production lines)
  - Real-time OEE dashboards
We currently track production manually in spreadsheets.
We expect ROI within 2 years and need full training for 60 operators.
"""


def package_deliverables(state: dict, zip_path: str):
    file_keys = [
        "discovery_report_path",
        "risk_assessment_path",
        "proposal_pdf_path",
        "asis_diagram_path",
        "tobe_diagram_path",
        "diagram_image_path",
        "solar_sequence_diagram_path",
        "hld_pdf_path",
        "digital_vision_path",
        "process_flow_document_path",
        "poc_plan_path",
        "commercial_proposal_path",
        "roadmap_pdf_path",
        "infrastructure_pdf_path",
        "roi_business_case_path",
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for key in file_keys:
            fpath = state.get(key)
            if fpath and os.path.exists(fpath):
                zf.write(fpath, os.path.basename(fpath))
    print(f"   ✓ All deliverables zipped → {zip_path}")


def run_presales(customer_query: str, output_dir: str = "output") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    state = {"customer_query": customer_query.strip()}

    # Step 1: Multi-agent debate
    print("\n[1/18] 🔍  Multi-agent requirement debate …")
    try:
        graph  = build_debate_graph()
        result = graph.invoke({"customer_query": customer_query})
        state["requirements"] = result.get("final_requirements") or result.get("requirements", {})
        print(f"   ✓  Requirements extracted")
    except Exception as exc:
        print(f"   ⚠️  Debate graph failed: {exc}. Using empty requirements.")
        state["requirements"] = {"industry": "Solar", "lines": 4, "machine_types": 20, "erp": "SAP"}

    # Step 2: Knowledge retrieval
    print("\n[2/18] 📚  Retrieving domain knowledge …")
    try:
        state = KnowledgeAgent().run(state)
        print("   ✓  Domain knowledge retrieved")
    except Exception as exc:
        print(f"   ⚠️  KnowledgeAgent failed: {exc}")
        state.setdefault("domain_knowledge", "")
        state.setdefault("roi_knowledge", "")

    # Step 3: Discovery Report (BRD)
    print("\n[3/18] 📄  Generating Discovery Report (BRD) …")
    try:
        state = DiscoveryReportAgent().run(state, os.path.join(output_dir, "discovery_report.pdf"))
        print(f"   ✓  {state['discovery_report_path']}")
    except Exception as exc:
        print(f"   ⚠️  DiscoveryReportAgent failed: {exc}")

    # Step 4: AS-IS / TO-BE process diagrams
    print("\n[4/18] 🔄  Generating AS-IS / TO-BE process diagrams …")
    try:
        state = ProcessFlowAgent().run(state)
    except Exception as exc:
        print(f"   ⚠️  ProcessFlowAgent failed: {exc}")
        state.setdefault("asis_diagram_path", None)
        state.setdefault("tobe_diagram_path", None)

    # Step 5: Solar manufacturing sequence diagram
    print("\n[5/18] 🔬  Generating solar manufacturing process sequence …")
    try:
        state = SolarProcessSequenceAgent().run(state)
    except Exception as exc:
        print(f"   ⚠️  Solar sequence agent failed: {exc}")
        state.setdefault("solar_sequence_diagram_path", None)

    # Step 6: High-Level Design (HLD)
    print("\n[6/18] 🏗️   Generating High-Level Design (HLD) …")
    try:
        highlevel_agent = HighLevelDesignAgent()
        state = highlevel_agent.run(state, os.path.join(output_dir, "high_level_design.pdf"))
    except Exception as exc:
        print(f"   ⚠️  HighLevelDesignAgent failed: {exc}")

    # Step 7: Architecture design (text)
    print("\n[7/18] 🏗️   Designing solution architecture narrative …")
    try:
        state = ArchitectAgent().run(state)
        print("   ✓  Architecture text generated")
    except Exception as exc:
        print(f"   ⚠️  ArchitectAgent failed: {exc}")
        state["architecture"] = ""

    # Step 8: Architecture diagram (PlantUML)
    print("\n[8/18] 🖼️   Rendering architecture diagram …")
    try:
        plantuml_code = DiagramAgent().run(state)
        diagram_path  = render_plantuml(plantuml_code, output_dir=output_dir)
        state["diagram_image_path"] = diagram_path
    except Exception as exc:
        print(f"   ⚠️  Diagram rendering failed: {exc}")
        state["diagram_image_path"] = None

    # Step 9: Digital Transformation Vision
    print("\n[9/18] 📘  Generating Digital Transformation Vision …")
    try:
        dv_agent = DigitalVisionAgent()
        state = dv_agent.run(state, os.path.join(output_dir, "digital_vision.pdf"))
    except Exception as exc:
        print(f"   ⚠️  Digital Vision failed: {exc}")

    # Step 10: Process Flow Document (AS‑IS / TO‑BE narrative + diagrams)
    print("\n[10/18] 📋  Generating Process Flow Document …")
    try:
        pf_agent = ProcessFlowDocumentAgent()
        state = pf_agent.run(state, os.path.join(output_dir, "process_flow.pdf"))
    except Exception as exc:
        print(f"   ⚠️  Process Flow Document failed: {exc}")

    # Step 11: PoC Plan
    print("\n[11/18] 🧪  Generating PoC Plan …")
    try:
        poc_agent = PoCPlanAgent()
        state = poc_agent.run(state, os.path.join(output_dir, "poc_plan.pdf"))
    except Exception as exc:
        print(f"   ⚠️  PoC Plan failed: {exc}")

    # Step 12: Commercial Proposal
    print("\n[12/18] 💵  Generating Commercial Proposal …")
    try:
        cp_agent = CommercialProposalAgent()
        state = cp_agent.run(state, os.path.join(output_dir, "commercial_proposal.pdf"))
    except Exception as exc:
        print(f"   ⚠️  Commercial Proposal failed: {exc}")

    # Step 13: Risk assessment
    print("\n[13/18] ⚠️   Generating Risk Assessment …")
    try:
        state = RiskAgent().run(state, os.path.join(output_dir, "risk_assessment.pdf"))
    except Exception as exc:
        print(f"   ⚠️  RiskAgent failed: {exc}")

    # Step 14: Effort & cost estimation
    print("\n[14/18] 💰  Estimating effort, cost & ROI …")
    try:
        state = EstimatorAgent().run(state)
        est = state["estimation"]
        print(f"   ✓  Cost: ${est['estimated_cost_usd']:,.0f}  |  "
              f"Duration: {est['total_duration_months']} months  |  "
              f"Payback: {est['roi'].get('payback_months','?')} months")
    except Exception as exc:
        print(f"   ⚠️  EstimatorAgent failed: {exc}")
        state["estimation"] = {
            "estimated_cost_usd": 0, "total_duration_months": 0,
            "total_effort_person_months": 0, "phase_breakdown": {}, "roi": {},
        }

    # Step 15: Implementation Roadmap
    print("\n[15/18] 🔀  Generating Implementation Roadmap …")
    try:
        rm_agent = ImplementationRoadmapAgent()
        state = rm_agent.run(state, os.path.join(output_dir, "implementation_roadmap.pdf"))
    except Exception as exc:
        print(f"   ⚠️  Implementation Roadmap failed: {exc}")

    # Step 16: Infrastructure & Deployment Architecture
    print("\n[16/18] 🖧  Generating Infrastructure & Deployment Architecture …")
    try:
        infra_agent = InfrastructureDeploymentAgent()
        state = infra_agent.run(state, os.path.join(output_dir, "infrastructure_deployment.pdf"))
    except Exception as exc:
        print(f"   ⚠️  Infrastructure Deployment failed: {exc}")

    # Step 17: Standalone ROI Business Case (detailed)
    print("\n[17/18] 📊  Generating ROI & Business Case document …")
    try:
        roi_agent = ROIBusinessCaseAgent()
        state = roi_agent.run(state, os.path.join(output_dir, "roi_business_case.pdf"))
    except Exception as exc:
        print(f"   ⚠️  ROI Business Case failed: {exc}")

    # Step 18: Final proposal PDF (must be after estimation)
    print("\n[18/18] 📑  Building final Proposal / SOW …")
    try:
        state = ProposalAgent().run(state, os.path.join(output_dir, "proposal.pdf"))
        print(f"   ✓  {state['proposal_pdf_path']}")
    except Exception as exc:
        print(f"   ⚠️  ProposalAgent failed: {exc}")

    # Packaging
    print("\n📦  Packaging deliverables …")
    package_deliverables(state, os.path.join(output_dir, "solution_package.zip"))
    return state


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else DEFAULT_QUERY
    print("=" * 65)
    print("  AI Pre-Sales Consultant — Manufacturing Edition (v3.0)")
    print("=" * 65)
    print(f"\nQuery:\n{query.strip()}\n")
    final_state = run_presales(query)
    print("\n" + "=" * 65)
    print("  ✅ Pipeline complete. Deliverables in ./output/")
    print("=" * 65)
    import pprint
    pprint.pprint(final_state.get("estimation", {}))