"""
api/workflow.py
----------------
Background workflow — runs in threads, broadcasts progress via WebSocket.
Calls existing main.run_presales() for all document generation.
"""
import asyncio, builtins, json, os, sys, threading, traceback
from datetime import datetime
from typing import Dict, Set

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api.session_store import store

_ws: Dict[str, Set] = {}
_lock = threading.Lock()

def register_ws(sid, ws):
    with _lock:
        _ws.setdefault(sid, set()).add(ws)

def unregister_ws(sid, ws):
    with _lock:
        _ws.get(sid, set()).discard(ws)

async def _broadcast(sid, msg):
    with _lock:
        conns = list(_ws.get(sid, set()))
    for ws in conns:
        try:
            await ws.send_json(msg)
        except Exception:
            pass

def _emit(sid, progress, step, status=None, message="", data=None):
    upd = {"progress": progress, "current_step": step}
    if status:
        upd["status"] = status
    store.update(sid, **upd)
    payload = {"type": "progress", "session_id": sid, "progress": progress,
               "step": step, "message": message, "data": data or {},
               "timestamp": datetime.utcnow().isoformat()}
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_broadcast(sid, payload))
        loop.close()
    except Exception:
        pass


# ── Stage 1: CrewAI analysis → requirements + questions ─────────────────────

def _run_analysis(sid):
    try:
        store.update(sid, status="analyzing")
        _emit(sid, 5, "Initialising AI agents", "analyzing", "Starting CrewAI crew...")

        from crews.presales_crew import PresalesCrew
        session = store.get(sid)

        _emit(sid, 20, "Classifying industry", message="Identifying manufacturing domain...")
        crew = PresalesCrew(session["customer_query"])

        _emit(sid, 40, "Extracting requirements", message="Analysing your requirements...")
        result = crew.run_analysis()

        _emit(sid, 75, "Generating questions", message="Identifying gaps...")

        store.update(sid,
            requirements=result.get("requirements", {}),
            clarifying_questions=result.get("clarifying_questions", []),
            industry=result.get("requirements", {}).get("industry", "Manufacturing"),
            status="questioning", progress=80,
            current_step="Questions ready — awaiting your input")

        _emit(sid, 80, "Questions ready", "questioning",
              "Please answer the clarifying questions to improve your documents.",
              data={"questions": result.get("clarifying_questions", []),
                    "requirements": result.get("requirements", {})})

    except Exception as e:
        store.update(sid, status="error", error=f"{e}\n{traceback.format_exc()}")
        _emit(sid, 0, "Error", "error", f"Analysis failed: {e}")


# ── Stage 2: Full document generation ────────────────────────────────────────

def _run_generation(sid):
    try:
        store.update(sid, status="generating")
        _emit(sid, 3, "Starting generation", "generating", "Preparing pipeline...")

        from crews.presales_crew import PresalesCrew
        from main import run_presales

        session  = store.get(sid)
        answers  = session.get("user_answers") or {}
        industry = session.get("industry", "Manufacturing")

        # Build enriched query from original + answers
        enriched = session["customer_query"]
        if answers:
            qa = "\n".join(f"Q: {q}\nA: {a}" for q, a in answers.items())
            enriched += f"\n\nCustomer clarifications:\n{qa}"

        # Stage 2a: Domain enrichment via CrewAI
        _emit(sid, 8, "Running domain analysis", message="CrewAI domain enrichment...")
        try:
            crew = PresalesCrew(enriched)
            domain_result = crew.run_domain_enrichment(industry)
        except Exception as de:
            print(f"Domain enrichment warning: {de}")
            domain_result = {}

        _emit(sid, 18, "Domain analysis complete", message="Starting document generation...")

        # Stage 2b: Run all 18 existing document agents
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", sid)
        os.makedirs(output_dir, exist_ok=True)

        # Progress steps mapped to document pipeline
        prog_steps = [
            (20, "Debating requirements"), (22, "Loading knowledge base"),
            (26, "Generating BRD"), (30, "Creating AS-IS/TO-BE diagrams"),
            (34, "Building sequence diagram"), (38, "Generating HLD document"),
            (42, "Designing architecture"), (46, "Rendering architecture diagram"),
            (50, "Writing Digital Vision"), (54, "Creating Process Flow document"),
            (58, "Building PoC Plan"), (62, "Writing Commercial Proposal"),
            (66, "Generating Risk Assessment"), (70, "Calculating ROI & costs"),
            (74, "Creating Implementation Roadmap"), (78, "Writing Infrastructure doc"),
            (84, "Generating ROI Business Case"), (90, "Compiling final Proposal/SOW"),
        ]
        step_idx = [0]
        orig_print = builtins.print

        def tracking_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            orig_print(*args, **kwargs)
            if step_idx[0] < len(prog_steps):
                pct, label = prog_steps[step_idx[0]]
                _emit(sid, pct, label, message=msg)
                step_idx[0] += 1

        builtins.print = tracking_print
        try:
            state = run_presales(enriched, output_dir=output_dir)
        finally:
            builtins.print = orig_print

        # Package info
        zip_path = os.path.join(output_dir, "solution_package.zip")

        # Document manifest
        doc_map = [
            ("discovery_report_path",      "01", "Discovery Report / BRD",           "Business requirements, stakeholders, NFRs, success criteria"),
            ("proposal_pdf_path",          "02", "Solution Proposal / SOW",           "14-section comprehensive statement of work"),
            ("digital_vision_path",        "03", "Digital Transformation Vision",     "Executive vision statement and business drivers"),
            ("hld_pdf_path",               "04", "High-Level Architecture",           "System architecture, integration, deployment, security"),
            ("process_flow_document_path", "05", "Process Flow (AS-IS / TO-BE)",      "Process transformation analysis with diagrams"),
            ("poc_plan_path",              "06", "Demo / PoC Plan",                   "4-week pilot scope, success metrics, responsibilities"),
            ("infrastructure_pdf_path",    "07", "Infrastructure & Deployment",       "Hardware BOM, network topology, OT/IT segregation, DR"),
            ("roadmap_pdf_path",           "08", "Implementation Roadmap",            "7-phase plan, 52-week Gantt, RACI matrix, milestones"),
            ("risk_assessment_path",       "09", "Risk Assessment",                   "Colour-coded risk register with mitigations"),
            ("commercial_proposal_path",   "10", "Commercial Proposal",               "Pricing, payment schedule, team structure, terms"),
            ("roi_business_case_path",     "11", "ROI & Business Case",               "5-year financial analysis, scenarios, benchmarks"),
            ("asis_diagram_path",          "12", "AS-IS Process Diagram",             "Current state process flow"),
            ("tobe_diagram_path",          "13", "TO-BE Process Diagram",             "Future MES-integrated process flow"),
            ("solar_sequence_diagram_path","14", "Manufacturing Sequence Diagram",    "End-to-end manufacturing sequence"),
            ("diagram_image_path",         "15", "System Architecture Diagram",       "Component architecture diagram"),
        ]
        documents = []
        for key, num, name, desc in doc_map:
            fp = state.get(key)
            documents.append({
                "id": key, "num": num, "name": name, "description": desc,
                "file_path": fp,
                "status": "generated" if (fp and os.path.exists(fp)) else "failed",
                "feedback": None,
                "approved": False,
            })

        generated = sum(1 for d in documents if d["status"] == "generated")

        store.update(sid,
            status="reviewing", documents=documents,
            requirements=state.get("requirements", session.get("requirements")),
            zip_path=zip_path, progress=95,
            current_step=f"Review ready — {generated}/15 documents generated")

        _emit(sid, 95, "Documents ready", "reviewing",
              f"{generated} documents generated. Please review and approve.",
              data={"document_count": generated, "total": len(documents)})

    except Exception as e:
        store.update(sid, status="error", error=f"{e}\n{traceback.format_exc()}")
        _emit(sid, 0, "Error", "error", f"Generation failed: {e}")


def start_analysis(sid):
    threading.Thread(target=_run_analysis, args=(sid,), daemon=True).start()

def start_generation(sid):
    threading.Thread(target=_run_generation, args=(sid,), daemon=True).start()
