"""FastAPI app. Run: uvicorn app.main:app --reload  (from backend/)"""
import json

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.fusion.model import fusion_info
from app.ingest.email_parser import parse_eml
from app.llm import client as llm_client
from app.pipeline import analyze
from app.rag import index as rag
from app.schemas import AnalyzeRequest, AnalyzeResponse, Example
from app.signals.classifier import get_classifier

app = FastAPI(title="VisaShield API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MAX_UPLOAD = 8 * 1024 * 1024
SITUATIONS = {"not_responded", "paid", "shared_info"}


@app.on_event("startup")
def _warm() -> None:
    # Load models once so the first request isn't slow.
    get_classifier()
    if rag.available():
        rag.retrieve("warm up", k=1)


@app.get("/api/health")
def health():
    clf = get_classifier()
    return {
        "status": "ok",
        "llm_available": llm_client.available(),
        "classifier_loaded": clf.name != "none",
        "classifier": clf.name,
        "fusion": fusion_info(),
        "rag_available": rag.available(),
        "stt_available": _stt_available(),
    }


def _stt_available() -> bool:
    from app.ingest import stt

    return stt.available()


@app.get("/api/examples", response_model=list[Example])
def examples():
    if config.EXAMPLES_PATH.exists():
        return json.loads(config.EXAMPLES_PATH.read_text(encoding="utf-8"))
    return []


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeRequest):
    return await run_in_threadpool(analyze, req.text, req.language, req.situation)


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File too large (max 8 MB).")
    return data


@app.post("/api/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(file: UploadFile = File(...), language: str = Form("en"), situation: str = Form("not_responded")):
    from app.ingest.ocr import image_to_text

    data = await _read_upload(file)
    try:
        text = await run_in_threadpool(image_to_text, data)
    except Exception:
        raise HTTPException(400, "Could not read that image. Try a PNG or JPG screenshot.")
    if len(text.strip()) < 10:
        raise HTTPException(422, "We couldn't find readable text in that image. Try pasting the text instead.")
    situation = situation if situation in SITUATIONS else "not_responded"
    return await run_in_threadpool(analyze, text, language, situation, None, text)


MAX_AUDIO = 20 * 1024 * 1024  # Whisper API upload limit is 25 MB


@app.post("/api/analyze/audio", response_model=AnalyzeResponse)
async def analyze_audio(file: UploadFile = File(...), language: str = Form("en"), situation: str = Form("not_responded")):
    import os

    from app.ingest import stt

    if not stt.available():
        raise HTTPException(503, "Voice transcription isn't configured on this server.")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in stt.AUDIO_EXTS:
        raise HTTPException(415, "Unsupported audio format. Try MP3, M4A, WAV, OGG or WEBM.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > MAX_AUDIO:
        raise HTTPException(413, "Recording too large (max 20 MB, about 20 minutes).")
    try:
        transcript, _ = await run_in_threadpool(stt.transcribe, data, file.filename or f"audio{ext}")
    except Exception:
        raise HTTPException(502, "Couldn't transcribe that recording. Try again, or paste what the caller said.")
    if len(transcript) < 10:
        raise HTTPException(422, "We couldn't hear any speech in that recording.")
    situation = situation if situation in SITUATIONS else "not_responded"
    # Same framing the classifier saw in training ("Voicemail: ...", "Call transcript: ...").
    return await run_in_threadpool(analyze, f"Voicemail: {transcript}", language, situation, None, transcript)


@app.post("/api/analyze/email", response_model=AnalyzeResponse)
async def analyze_email(file: UploadFile = File(...), language: str = Form("en"), situation: str = Form("not_responded")):
    data = await _read_upload(file)
    text, meta = parse_eml(data)
    situation = situation if situation in SITUATIONS else "not_responded"
    return await run_in_threadpool(analyze, text, language, situation, meta)


@app.post("/api/webhooks/agentboxd")
async def agentboxd_webhook(request: Request, background: BackgroundTasks):
    from app.integrations.agentboxd import handle_webhook

    return await handle_webhook(request, background)


# Serve the built frontend (single-container deploy) when frontend/dist exists.
if config.FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        target = config.FRONTEND_DIST / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(config.FRONTEND_DIST / "index.html")
