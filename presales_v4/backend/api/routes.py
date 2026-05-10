"""
api/routes.py — All REST + WebSocket endpoints
"""
import os, sys, uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api.models import AnswerRequest, IntakeRequest, KnowledgeBaseCreate, ReviewDecision
from api.session_store import store
from api.workflow import register_ws, start_analysis, start_generation, unregister_ws

router = APIRouter()

# ── Sessions ──────────────────────────────────────────────────────────────────

@router.post("/sessions/start")
async def start_session(req: IntakeRequest, bg: BackgroundTasks):
    sid = str(uuid.uuid4())[:8]
    store.create(sid, req.query)
    bg.add_task(start_analysis, sid)
    return {"session_id": sid, "status": "analyzing",
            "message": "Session started. Analysing requirements..."}

@router.get("/sessions")
async def list_sessions():
    return store.list_all()

@router.get("/sessions/{sid}")
async def get_session(sid: str):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    return s

@router.post("/sessions/{sid}/answer")
async def submit_answers(sid: str, req: AnswerRequest, bg: BackgroundTasks):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    if s["status"] not in ("questioning", "intake", "analyzing", "error"):
        raise HTTPException(400, f"Cannot answer in '{s['status']}' state")
    store.update(sid, user_answers=req.answers, status="generating")
    bg.add_task(start_generation, sid)
    return {"session_id": sid, "status": "generating",
            "message": "Answers received. Generating all documents..."}

@router.post("/sessions/{sid}/skip-questions")
async def skip_questions(sid: str, bg: BackgroundTasks):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    store.update(sid, status="generating")
    bg.add_task(start_generation, sid)
    return {"session_id": sid, "status": "generating",
            "message": "Generating documents with available information..."}

@router.post("/sessions/{sid}/review")
async def submit_review(sid: str, req: ReviewDecision):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    if s["status"] not in ("reviewing", "approved"):
        raise HTTPException(400, f"Session not in review state (current: {s['status']})")

    if req.decision == "approve":
        docs = s.get("documents", [])
        for d in docs:
            if req.document_feedback and d["id"] in req.document_feedback:
                d["feedback"] = req.document_feedback[d["id"]]
            d["approved"] = True
        store.update(sid, status="approved", review_comments=req.comments,
                     documents=docs, progress=99, current_step="Approved — ready to publish")
        return {"message": "All documents approved. Ready to publish.", "status": "approved"}

    elif req.decision == "request_changes":
        store.update(sid, review_comments=req.comments,
                     current_step="Changes requested")
        return {"message": "Changes noted. Please regenerate.", "status": s["status"]}

    elif req.decision == "reject":
        store.update(sid, status="intake", review_comments=req.comments,
                     progress=0, current_step="Rejected — please restart")
        return {"message": "Rejected. Start a new query.", "status": "intake"}

    raise HTTPException(400, f"Unknown decision: {req.decision}")

@router.post("/sessions/{sid}/approve-document")
async def approve_document(sid: str, doc_id: str, feedback: str = ""):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    docs = s.get("documents", [])
    for d in docs:
        if d["id"] == doc_id:
            d["approved"] = True
            d["feedback"] = feedback
    store.update(sid, documents=docs)
    return {"message": f"Document {doc_id} approved"}

@router.post("/sessions/{sid}/publish")
async def publish(sid: str):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    if s["status"] not in ("approved", "reviewing"):
        raise HTTPException(400, "Must be approved before publishing")
    store.update(sid, status="published", progress=100, current_step="Published")
    return {"message": "Package published", "status": "published",
            "download_url": f"/api/sessions/{sid}/download"}

@router.get("/sessions/{sid}/download")
async def download_package(sid: str):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    zp = s.get("zip_path") or os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "output", sid, "solution_package.zip")
    if not os.path.exists(zp):
        raise HTTPException(404, "Package not yet generated")
    return FileResponse(zp, media_type="application/zip",
                        filename=f"presales_package_{sid}.zip")

@router.get("/sessions/{sid}/document/{doc_id}")
async def download_doc(sid: str, doc_id: str):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    doc = next((d for d in s.get("documents", []) if d["id"] == doc_id), None)
    if not doc or not doc.get("file_path"): raise HTTPException(404, "Document not found")
    fp = doc["file_path"]
    if not os.path.exists(fp): raise HTTPException(404, "File not found")
    ext = os.path.splitext(fp)[1].lower()
    return FileResponse(fp,
        media_type="application/pdf" if ext == ".pdf" else "image/png",
        filename=os.path.basename(fp))

@router.get("/sessions/{sid}/preview/{doc_id}")
async def preview_doc(sid: str, doc_id: str):
    s = store.get(sid)
    if not s: raise HTTPException(404, "Session not found")
    doc = next((d for d in s.get("documents", []) if d["id"] == doc_id), None)
    if not doc or not doc.get("file_path"): raise HTTPException(404, "Document not found")
    fp = doc["file_path"]
    if not os.path.exists(fp): raise HTTPException(404, "File not found")
    ext = os.path.splitext(fp)[1].lower()
    return FileResponse(fp,
        media_type="application/pdf" if ext == ".pdf" else "image/png",
        headers={"Content-Disposition": "inline"})

# ── Knowledge Base ────────────────────────────────────────────────────────────

@router.get("/industries")
async def list_industries():
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    industries = [{"id": "solar", "name": "Solar Manufacturing",
                   "description": "Solar PV panel / module manufacturing (ALMM compliant)"}]
    try:
        for d in sorted(os.listdir(base)):
            fp = os.path.join(base, d)
            if os.path.isdir(fp) and os.path.exists(os.path.join(fp, "knowledge.txt")):
                industries.append({"id": d, "name": d.replace("_"," ").title(),
                                   "description": f"{d.replace('_',' ').title()} manufacturing"})
    except Exception:
        pass
    return industries

@router.post("/knowledge-base")
async def create_kb(req: KnowledgeBaseCreate):
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    slug = req.industry.lower().replace(" ", "_")
    dir_ = os.path.join(base, slug)
    os.makedirs(dir_, exist_ok=True)
    path = os.path.join(dir_, "knowledge.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {req.industry} Manufacturing Knowledge Base\n")
        if req.description:
            f.write(f"# {req.description}\n\n")
        f.write(req.content)
    return {"message": f"Knowledge base saved for {req.industry}", "path": path}

@router.get("/knowledge-base/{industry}")
async def get_kb(industry: str):
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    slug = industry.lower().replace(" ", "_")
    for p in [os.path.join(base, slug, "knowledge.txt"),
               os.path.join(base, "industry_knowledge.txt")]:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return {"industry": industry, "content": f.read(), "path": p}
    raise HTTPException(404, f"No knowledge base for {industry}")

# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws/{sid}")
async def ws_endpoint(ws: WebSocket, sid: str):
    await ws.accept()
    register_ws(sid, ws)
    s = store.get(sid)
    if s:
        await ws.send_json({"type": "state", "session_id": sid, "data": s})
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        unregister_ws(sid, ws)
