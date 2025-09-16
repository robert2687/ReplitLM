import os
import json
import zipfile
from pathlib import Path


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def write_file(path: str, content: str):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_app_file(framework: str, prompt: str, code: str, target_dir: str, app_filename: str = "app.py"):
    # Minimal project scaffolding per framework
    if framework == "streamlit":
        write_file(os.path.join(target_dir, app_filename), _wrap_streamlit(code))
        write_file(os.path.join(target_dir, "requirements.txt"), "streamlit\n")
        write_file(os.path.join(target_dir, "README.md"), f"# Generated Streamlit App\n\nPrompt:\n\n```\n{prompt}\n```")
    elif framework == "gradio":
        write_file(os.path.join(target_dir, app_filename), _wrap_gradio(code))
        write_file(os.path.join(target_dir, "requirements.txt"), "gradio\n")
        write_file(os.path.join(target_dir, "README.md"), f"# Generated Gradio App\n\nPrompt:\n\n```\n{prompt}\n```")
    else:
        # raw python script
        write_file(os.path.join(target_dir, app_filename), code)
        write_file(os.path.join(target_dir, "requirements.txt"), "")
        write_file(os.path.join(target_dir, "README.md"), f"# Generated App\n\nPrompt:\n\n```\n{prompt}\n```")

    # Add a simple run script
    run_sh = "streamlit run app.py\n" if framework == "streamlit" else "python app.py\n"
    write_file(os.path.join(target_dir, "run.sh"), run_sh)
    # Add .gitignore to keep zips and caches out
    write_file(os.path.join(target_dir, ".gitignore"), "__pycache__/\n*.pyc\n.env\n.venv/\n*.zip\n")


def _wrap_streamlit(code: str) -> str:
    # If the model produced only a function, ensure Streamlit can run
    header = (
        "import streamlit as st\n"
        "st.set_page_config(page_title='AI App Builder', layout='wide')\n"
        "\n"
        "# Generated with AI App Builder\n"
    )
    if "streamlit" in code or "st." in code:
        return header + "\n" + code
    # Provide a basic wrapper if plain python was produced
    body = (
        "\n"
        "st.title('Your Generated App')\n"
        "st.write('Below is the generated code output rendered in a text area. You can copy and adapt it:')\n"
        "st.code('''\\\n" + code.replace(\"'''\", \"\\'\\'\\'\") + "\\n''', language='python')\n"
    )
    return header + body


def _wrap_gradio(code: str) -> str:
    header = "# Generated with AI App Builder\n"
    if "gradio" in code or "gr.Interface" in code or "import gradio as gr" in code:
        return header + "\n" + code
    # Minimal gradio shell
    skeleton = (
        "import gradio as gr\n"
        "\n"
        "def run():\n"
        "    return 'Replace this with your logic.'\n"
        "\n"
        "demo = gr.Interface(fn=run, inputs=[], outputs='text', title='Your Generated App')\n"
        "demo.launch()\n"
    )
    return header + skeleton


def make_zip_from_dir(src_dir: str, base_name: str) -> str:
    zip_path = f"{base_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src_dir)
                zf.write(full, rel)
    return zip_path