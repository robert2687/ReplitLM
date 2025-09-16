import os
import tempfile
import threading
import asyncio
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .generator import CodeGenerator
from .utils import write_app_file, make_zip_from_dir
from .jobs import JobStore


app = FastAPI(title="AI App Builder")
base_dir = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

# Single, lazy-loaded generator shared across requests
generator = CodeGenerator(model_path=os.path.join(base_dir, "..", "replit-code-v1-3b"))

# Limit concurrency to avoid OOM
_max_concurrency = int(os.getenv("APP_MAX_CONCURRENCY", "1"))
_semaphore = threading.BoundedSemaphore(_max_concurrency)


@app.on_event("startup")
async def _startup():
    # start background pruner
    JobStore.start_pruner()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


# Simple background worker for generation
def _run_job(job_id: str):
    job = JobStore.get(job_id)
    if not job:
        return
    # always acquire exactly once (non-blocking, then blocking if needed)
    got = _semaphore.acquire(blocking=False)
    try:
        if not got:
            JobStore.update(job_id, status="queued", message="Waiting for available worker…", progress=0.0)
            _semaphore.acquire()
        JobStore.update(job_id, status="running", message="Loading model…", progress=0.1)
        completion = asyncio.run(generator.generate_code(prompt=job.prompt, framework=job.framework))
        JobStore.set_progress(job_id, 0.6, "Scaffolding project…")

        workdir = tempfile.mkdtemp(prefix="ai-app-")
        write_app_file(framework=job.framework, prompt=job.prompt, code=completion, target_dir=workdir, app_filename="app.py")
        JobStore.set_progress(job_id, 0.85, "Packaging…")
        zip_path = make_zip_from_dir(workdir, base_name=os.path.join(tempfile.gettempdir(), os.path.basename(workdir)))
        JobStore.update(job_id, status="succeeded", progress=1.0, message="Done", zip_path=zip_path)
    except Exception as e:
        JobStore.update(job_id, status="failed", message=str(e))
    finally:
        try:
            _semaphore.release()
        except ValueError:
            pass


@app.post("/api/jobs")
async def create_job(prompt: str = Form(...), framework: str = Form("streamlit")):
    prompt = (prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if framework not in {"streamlit", "gradio", "python"}:
        raise HTTPException(status_code=400, detail="Invalid framework")
    # length cap to prevent extremely long prompts
    if len(prompt) > 4000:
        raise HTTPException(status_code=400, detail="Prompt too long (max 4000 chars)")
    job = JobStore.create(prompt=prompt, framework=framework)
    # Use a thread to avoid blocking the event loop for long generations
    t = threading.Thread(target=_run_job, args=(job.id,), daemon=True)
    t.start()
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = JobStore.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "message": job.message,
        "progress": job.progress,
    }


@app.get("/api/jobs/{job_id}/download")
async def download(job_id: str, background: BackgroundTasks):
    job = JobStore.get(job_id)
    if not job or job.status != "succeeded" or not job.zip_path:
        raise HTTPException(status_code=404, detail="Not ready")

    path = job.zip_path

    def _cleanup():
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        # clear zip path but keep job for a short TTL until pruned
        JobStore.update(job_id, zip_path=None, message="Downloaded")

    background.add_task(_cleanup)

    return FileResponse(
        path,
        media_type="application/zip",
        filename=os.path.basename(path),
        background=background,
    )