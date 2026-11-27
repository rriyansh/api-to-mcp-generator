import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "src" / "templates"
OUTPUT_DIR = BASE_DIR / "output"
SERVER_FILE = OUTPUT_DIR / "generated_mcp_server.py"
CONFIG_FILE = OUTPUT_DIR / "claude_desktop_config.json"
ENV_FILE = OUTPUT_DIR / ".env.example"


def render_server(data):
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = environment.get_template("server_template.py.j2")
    return template.render(**data)


def build_config(data):
    config = {
        "mcpServers": {
            data["tool_name"]: {
                "command": sys.executable,
                "args": [str(SERVER_FILE)],
            }
        }
    }
    return json.dumps(config, indent=2)


def build_env_example(data):
    lines = [f"{name}=your_value_here" for name in data["env_vars"]]
    return "\n".join(lines) + "\n"


def generate_files(data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    server_code = render_server(data)
    config_text = build_config(data)

    SERVER_FILE.write_text(server_code, encoding="utf-8")
    CONFIG_FILE.write_text(config_text, encoding="utf-8")

    env_text = ""
    if data["env_vars"]:
        env_text = build_env_example(data)
        ENV_FILE.write_text(env_text, encoding="utf-8")

    return {
        "server_code": server_code,
        "config_text": config_text,
        "env_text": env_text,
        "server_path": str(SERVER_FILE),
        "config_path": str(CONFIG_FILE),
    }
