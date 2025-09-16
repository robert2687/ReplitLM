import os
import tempfile
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from .generator import CodeGenerator
from .utils import write_app_file, make_zip_from_dir


app = FastAPI(title="AI App Builder")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Single, lazy-loaded generator shared across requests
generator = CodeGenerator(model_path=os.path.join(os.path.dirname(__file__), "..", "replit-code-v1-3b"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate(prompt: str = Form(...), framework: str = Form("streamlit")):
    # Create a temp working directory for this build
    workdir = tempfile.mkdtemp(prefix="ai-app-")
    app_filename = "app.py"

    completion = await generator.generate_code(prompt=prompt, framework=framework)

    # Persist the generated app into a project structure
    write_app_file(framework=framework, prompt=prompt, code=completion, target_dir=workdir, app_filename=app_filename)

    # Zip the project for download
    zip_path = make_zip_from_dir(workdir, base_name=os.path.join(tempfile.gettempdir(), os.path.basename(workdir)))

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{os.path.basename(workdir)}.zip",
    )