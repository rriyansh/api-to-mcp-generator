import ipaddress
import keyword
import re
from urllib.parse import parse_qsl, urlparse

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
ENV_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,59}$")
HEADER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,60}$")
QUERY_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

MAX_TOOLS = 10
MAX_PARAMETERS = 20
MAX_HEADERS = 10
MAX_DESCRIPTION = 500
MAX_PARAMETER_DESCRIPTION = 200
MAX_URL_LENGTH = 2000

ALLOWED_METHODS = ["GET", "POST"]
ALLOWED_LOCATIONS = ["query", "body"]
AUTH_TYPES = ["none", "bearer", "api_key_header", "api_key_query"]
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
SECRET_QUERY_NAMES = [
    "key",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "auth",
    "secret",
    "client_secret",
    "password",
    "signature",
]
RESERVED_NAMES = [
    "os",
    "re",
    "requests",
    "mcp",
    "Optional",
    "Annotated",
    "Field",
    "FastMCP",
    "load_dotenv",
    "PLACEHOLDER",
    "REQUEST_TIMEOUT",
    "MAX_RESPONSE_CHARS",
    "resolve_all",
    "clean_query",
    "send_request",
]
TRUE_WORDS = ["yes", "y", "true", "1"]
FALSE_WORDS = ["no", "n", "false", "0"]


class ParserError(ValueError):
    pass


def clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("nan", "none"):
        return ""
    return text


def to_bool(value, default):
    text = clean_text(value).lower()
    if text in TRUE_WORDS:
        return True
    if text in FALSE_WORDS:
        return False
    return default


def validate_name(value, label):
    if not value:
        raise ParserError(f"{label} cannot be empty.")
    if not IDENTIFIER_PATTERN.match(value):
        raise ParserError(
            f"{label} '{value}' can only use letters, numbers and underscores, and cannot start with a number."
        )
    if value.startswith("_"):
        raise ParserError(f"{label} '{value}' cannot start with an underscore.")
    if keyword.iskeyword(value) or value in RESERVED_NAMES:
        raise ParserError(f"{label} '{value}' is a reserved word. Please choose another name.")
    return value


def validate_server_name(value):
    value = clean_text(value)
    if not SERVER_NAME_PATTERN.match(value):
        raise ParserError(
            "Server name must start with a letter and use only letters, numbers, hyphens and underscores (maximum 40 characters)."
        )
    return value


def validate_description(description):
    if not description:
        raise ParserError("Tool description cannot be empty.")
    if len(description) > MAX_DESCRIPTION:
        raise ParserError(f"Tool description is longer than {MAX_DESCRIPTION} characters.")
    return description


def validate_method(http_method):
    http_method = http_method.upper()
    if http_method not in ALLOWED_METHODS:
        raise ParserError("HTTP method must be GET or POST.")
    return http_method


def validate_auth_type(auth_type):
    if auth_type not in AUTH_TYPES:
        raise ParserError("Unknown authentication type.")
    return auth_type


def is_private_host(hostname):
    lowered = hostname.lower()
    if lowered == "localhost" or lowered.endswith((".localhost", ".local", ".internal")):
        return True
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def validate_url(api_url, uses_auth, allow_private):
    warnings = []
    if not api_url or len(api_url) > MAX_URL_LENGTH:
        raise ParserError("API URL is missing or too long.")
    if any(character.isspace() for character in api_url):
        raise ParserError("API URL cannot contain spaces.")
    try:
        parsed = urlparse(api_url)
        hostname = parsed.hostname
    except ValueError:
        raise ParserError("API URL is not valid.") from None
    if parsed.scheme not in ("http", "https") or not hostname:
        raise ParserError("API URL must start with http:// or https:// and include a host name.")
    if parsed.username or parsed.password:
        raise ParserError(
            "Do not put a username or password inside the URL. Use the Authentication setting instead."
        )
    for name, _ in parse_qsl(parsed.query, keep_blank_values=True):
        if name.lower().replace("-", "_") in SECRET_QUERY_NAMES:
            raise ParserError(
                f"The URL contains '{name}', which looks like a secret. Remove it and choose 'API key in the URL query' as the authentication type."
            )
    private = is_private_host(hostname)
    if private and not allow_private:
        raise ParserError(
            "This URL points to a local or private network address. Tick 'Allow local and private network URLs' only if the API runs on your own computer."
        )
    if parsed.scheme == "http":
        if uses_auth and not private:
            raise ParserError("Authentication over plain http:// is not allowed. Use https:// instead.")
        warnings.append(f"{api_url} uses plain http://, so the traffic is not encrypted.")
    return api_url, warnings


def add_header(headers, name, value):
    for existing in headers:
        if existing.lower() == name.lower():
            raise ParserError(f"Header '{name}' is set more than once.")
    if len(headers) >= MAX_HEADERS:
        raise ParserError(f"A tool can have at most {MAX_HEADERS} headers.")
    headers[name] = value


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
        if any(ord(character) < 32 for character in value):
            raise ParserError(f"Header '{name}' contains control characters.")
        if name.lower() in SECRET_HEADERS and not ENV_PATTERN.search(value):
            raise ParserError(
                f"Header '{name}' looks like a secret. Do not type the real key here. "
                f"Use the Authentication setting instead."
            )
        add_header(headers, name, value)
    return headers


def apply_auth(auth_type, raw, headers, auth_query):
    if auth_type == "none":
        return
    env_name = clean_text(raw.get("auth_env"))
    if not ENV_NAME_PATTERN.match(env_name):
        raise ParserError(
            "The environment variable name must use capital letters, numbers and underscores, for example API_TOKEN."
        )
    placeholder = "${" + env_name + "}"
    if auth_type == "bearer":
        add_header(headers, "Authorization", "Bearer " + placeholder)
    elif auth_type == "api_key_header":
        header_name = clean_text(raw.get("auth_name"))
        if not HEADER_NAME_PATTERN.match(header_name):
            raise ParserError("The API key header name is missing or has invalid characters.")
        add_header(headers, header_name, placeholder)
    else:
        query_name = clean_text(raw.get("auth_name"))
        if not QUERY_NAME_PATTERN.match(query_name):
            raise ParserError("The API key query parameter name is missing or has invalid characters.")
        auth_query[query_name] = placeholder


def parse_parameters(rows, http_method):
    parameters = []
    seen_names = set()
    for row in rows:
        name_text = clean_text(row.get("name"))
        if not name_text:
            continue
        if len(parameters) >= MAX_PARAMETERS:
            raise ParserError(f"A tool can have at most {MAX_PARAMETERS} parameters.")
        name = validate_name(name_text, "Parameter name")
        if name in seen_names:
            raise ParserError(f"Parameter name '{name}' is used more than once.")
        seen_names.add(name)
        param_type = clean_text(row.get("type")).lower() or "string"
        if param_type not in TYPE_MAP:
            raise ParserError(f"Type '{param_type}' of '{name}' must be string, integer, number or boolean.")
        location = clean_text(row.get("location")).lower() or "query"
        if location not in ALLOWED_LOCATIONS:
            raise ParserError(f"Location '{location}' of '{name}' must be query or body.")
        if http_method == "GET" and location == "body":
            raise ParserError(f"GET requests cannot have body parameters. Change '{name}' to query.")
        description = clean_text(row.get("description")) or f"Value for {name}"
        if len(description) > MAX_PARAMETER_DESCRIPTION:
            raise ParserError(f"Description of '{name}' is longer than {MAX_PARAMETER_DESCRIPTION} characters.")
        parameters.append(
            {
                "name": name,
                "type": param_type,
                "python_type": TYPE_MAP[param_type],
                "location": location,
                "required": to_bool(row.get("required"), True),
                "description": description,
                "example": clean_text(row.get("example")),
            }
        )
    required_parameters = [item for item in parameters if item["required"]]
    optional_parameters = [item for item in parameters if not item["required"]]
    return required_parameters + optional_parameters


def find_env_vars(headers, auth_query):
    names = set()
    for value in list(headers.values()) + list(auth_query.values()):
        for match in ENV_PATTERN.finditer(value):
            names.add(match.group(1))
    return sorted(names)


def parse_tool(raw, allow_private):
    name = validate_name(clean_text(raw.get("name")), "Tool name")
    description = validate_description(clean_text(raw.get("description")))
    method = validate_method(clean_text(raw.get("method")) or "GET")
    auth_type = validate_auth_type(clean_text(raw.get("auth_type")) or "none")
    api_url, warnings = validate_url(clean_text(raw.get("url")), auth_type != "none", allow_private)
    headers = parse_headers(str(raw.get("headers_text") or ""))
    auth_query = {}
    apply_auth(auth_type, raw, headers, auth_query)
    parameters = parse_parameters(raw.get("params") or [], method)
    tool = {
        "name": name,
        "description": description,
        "api_url": api_url,
        "http_method": method,
        "headers": headers,
        "auth_query": auth_query,
        "parameters": parameters,
        "env_vars": find_env_vars(headers, auth_query),
    }
    return tool, warnings


def parse_server(server_name, tools_raw, allow_private=False):
    clean_server_name = validate_server_name(server_name)
    if not tools_raw:
        raise ParserError("Add at least one tool.")
    if len(tools_raw) > MAX_TOOLS:
        raise ParserError(f"A server can have at most {MAX_TOOLS} tools.")
    tools = []
    seen_names = set()
    warnings = []
    env_vars = set()
    for index, raw in enumerate(tools_raw, start=1):
        try:
            tool, tool_warnings = parse_tool(raw, allow_private)
        except ParserError as error:
            raise ParserError(f"Tool {index}: {error}") from None
        if tool["name"] in seen_names:
            raise ParserError(f"Tool {index}: the name '{tool['name']}' is already used by another tool.")
        seen_names.add(tool["name"])
        tools.append(tool)
        warnings.extend(tool_warnings)
        env_vars.update(tool["env_vars"])
    return {
        "server_name": clean_server_name,
        "tools": tools,
        "env_vars": sorted(env_vars),
        "warnings": warnings,
    }
