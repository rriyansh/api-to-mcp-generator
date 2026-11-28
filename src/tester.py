import importlib.util
import json
from pathlib import Path

from dotenv import load_dotenv


def load_server_module(server_path):
    load_dotenv(Path(server_path).parent / ".env", override=True)
    spec = importlib.util.spec_from_file_location("generated_server_under_test", server_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tool(server_path, tool_name, arguments_text):
    try:
        arguments = json.loads(arguments_text) if arguments_text.strip() else {}
    except json.JSONDecodeError as error:
        return False, f"The arguments are not valid JSON: {error}"
    if not isinstance(arguments, dict):
        return False, 'The arguments must be a JSON object, for example {"userId": 1}'
    try:
        module = load_server_module(server_path)
        tool_function = getattr(module, tool_name)
        return True, tool_function(**arguments)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
