"""
server.py — FastAPI entry point
Run: uvicorn server:app --reload --port 8000
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import router

app = FastAPI(title="AI Pre-Sales Consultant", version="4.0.0",
              description="Multi-agent AI system for manufacturing pre-sales")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "version": "4.0.0"}

# Serve React build if present
_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.exists(_build):
    app.mount("/", StaticFiles(directory=_build, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host=host, port=port, reload=True)
