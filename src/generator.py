import io
import json
import sys
import zipfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "src" / "templates"
OUTPUT_DIR = BASE_DIR / "output"

SAMPLE_VALUES = {
    "string": "example",
    "integer": 1,
    "number": 1.5,
    "boolean": True,
}


def create_environment():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_template(template_name, data):
    template = create_environment().get_template(template_name)
    return template.render(**data)


def build_requirements():
    return "mcp<2\npydantic\nrequests\npython-dotenv\n"


def build_env_example(data):
    lines = [f"{name}=your_value_here" for name in data["env_vars"]]
    return "\n".join(lines) + "\n"


def build_config(server_name, server_path, python_command):
    config = {
        "mcpServers": {
            server_name: {
                "command": python_command,
                "args": [server_path],
            }
        }
    }
    return json.dumps(config, indent=2)


def build_bundle(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def sample_value(parameter):
    text = parameter["example"]
    kind = parameter["type"]
    fallback = SAMPLE_VALUES[kind]
    if not text:
        return fallback
    try:
        if kind == "integer":
            return int(text)
        if kind == "number":
            return float(text)
    except ValueError:
        return fallback
    if kind == "boolean":
        return text.lower() in ("true", "yes", "1")
    return text


def sample_arguments(tool):
    return {item["name"]: sample_value(item) for item in tool["parameters"]}


def generate_files(data):
    folder = OUTPUT_DIR / data["server_name"]
    folder.mkdir(parents=True, exist_ok=True)

    server_path = str(folder / "server.py")
    python_command = sys.executable

    files = {
        "server.py": render_template("server_template.py.j2", data),
        "requirements.txt": build_requirements(),
        "claude_desktop_config.json": build_config(data["server_name"], server_path, python_command),
        "RUN_GUIDE.md": render_template("run_guide.md.j2", data),
    }
    env_file = folder / ".env.example"
    if data["env_vars"]:
        files[".env.example"] = build_env_example(data)
    elif env_file.exists():
        env_file.unlink()

    for name, content in files.items():
        (folder / name).write_text(content, encoding="utf-8")

    return {
        "files": files,
        "folder": str(folder),
        "server_path": server_path,
        "python_command": python_command,
        "zip_bytes": build_bundle(files),
    }
