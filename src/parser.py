import keyword
import re
from urllib.parse import urlparse

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
HEADER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

ALLOWED_METHODS = ["GET", "POST"]
ALLOWED_LOCATIONS = ["query", "body"]
TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}
SECRET_HEADERS = [
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "apikey",
    "x-auth-token",
]
RESERVED_NAMES = [
    "os",
    "re",
    "requests",
    "mcp",
    "Optional",
    "API_URL",
    "HEADERS",
    "resolve_value",
    "clean_query",
    "response",
    "error",
]
TRUE_WORDS = ["yes", "y", "true", "1"]
FALSE_WORDS = ["no", "n", "false", "0"]


class ParserError(ValueError):
    pass


def validate_name(value, label):
    value = value.strip()
    if not IDENTIFIER_PATTERN.match(value):
        raise ParserError(
            f"{label} '{value}' can only use letters, numbers and underscores, and cannot start with a number."
        )
    if value.startswith("_"):
        raise ParserError(f"{label} '{value}' cannot start with an underscore.")
    if keyword.iskeyword(value) or value in RESERVED_NAMES:
        raise ParserError(f"{label} '{value}' is a reserved word. Please choose another name.")
    return value


def validate_description(description):
    description = description.strip()
    if not description:
        raise ParserError("Tool description cannot be empty.")
    return description


def validate_url(api_url):
    api_url = api_url.strip()
    parsed = urlparse(api_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ParserError("API URL must start with http:// or https:// and include a host name.")
    return api_url


def validate_method(http_method):
    http_method = http_method.strip().upper()
    if http_method not in ALLOWED_METHODS:
        raise ParserError("HTTP method must be GET or POST.")
    return http_method


def parse_headers(headers_text):
    headers = {}
    for line in headers_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ParserError(f"Header line '{line}' must look like 'Name: value'.")
        name, value = line.split(":", 1)
        name = name.strip()
        value = value.strip()
        if not HEADER_NAME_PATTERN.match(name):
            raise ParserError(f"Header name '{name}' has invalid characters.")
        if not value:
            raise ParserError(f"Header '{name}' has no value.")
        if name.lower() in SECRET_HEADERS and not ENV_PATTERN.search(value):
            raise ParserError(
                f"Header '{name}' looks like a secret. Do not type the real key. "
                f"Use a placeholder such as 'Bearer ${{API_TOKEN}}' instead."
            )
        headers[name] = value
    return headers


def parse_required(text, line):
    text = text.strip().lower()
    if text in TRUE_WORDS:
        return True
    if text in FALSE_WORDS:
        return False
    raise ParserError(f"In '{line}', required must be yes or no.")


def parse_parameters(parameters_text, http_method):
    parameters = []
    seen_names = set()
    for line in parameters_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) > 4:
            raise ParserError(f"Parameter line '{line}' has too many parts. Use: name, type, location, required.")
        name = validate_name(parts[0], "Parameter name")
        if name in seen_names:
            raise ParserError(f"Parameter name '{name}' is used more than once.")
        seen_names.add(name)
        param_type = parts[1].lower() if len(parts) > 1 and parts[1] else "string"
        if param_type not in TYPE_MAP:
            raise ParserError(f"Type '{param_type}' in '{line}' must be string, integer, number or boolean.")
        location = parts[2].lower() if len(parts) > 2 and parts[2] else "query"
        if location not in ALLOWED_LOCATIONS:
            raise ParserError(f"Location '{location}' in '{line}' must be query or body.")
        if http_method == "GET" and location == "body":
            raise ParserError(f"GET requests cannot have body parameters. Change '{name}' to query.")
        required = parse_required(parts[3], line) if len(parts) > 3 and parts[3] else True
        parameters.append(
            {
                "name": name,
                "type": param_type,
                "python_type": TYPE_MAP[param_type],
                "location": location,
                "required": required,
            }
        )
    required_parameters = [item for item in parameters if item["required"]]
    optional_parameters = [item for item in parameters if not item["required"]]
    return required_parameters + optional_parameters


def find_env_vars(headers):
    names = set()
    for value in headers.values():
        for match in ENV_PATTERN.finditer(value):
            names.add(match.group(1))
    return sorted(names)


def parse_input(tool_name, description, api_url, http_method, headers_text, parameters_text):
    clean_method = validate_method(http_method)
    headers = parse_headers(headers_text)
    return {
        "tool_name": validate_name(tool_name, "Tool name"),
        "description": validate_description(description),
        "api_url": validate_url(api_url),
        "http_method": clean_method,
        "headers": headers,
        "parameters": parse_parameters(parameters_text, clean_method),
        "env_vars": find_env_vars(headers),
    }
