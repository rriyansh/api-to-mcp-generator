
import copy

import pandas as pd
import streamlit as st

from src.presets import BLANK_TOOL, PRESETS

PARAM_COLUMNS = ["name", "type", "location", "required", "description", "example"]
TYPE_OPTIONS = ["string", "integer", "number", "boolean"]
LOCATION_OPTIONS = ["query", "body"]
METHODS = ["GET", "POST"]
AUTH_LABELS = {
    "none": "No authentication",
    "bearer": "Bearer token",
    "api_key_header": "API key in a header",
    "api_key_query": "API key in the URL query",
}
AUTH_KEYS = list(AUTH_LABELS)
DEFAULT_PRESET = "JSONPlaceholder (GET and POST)"


def next_uid():
    st.session_state["next_uid"] = st.session_state.get("next_uid", 0) + 1
    return st.session_state["next_uid"]


def new_tool(template):
    tool = copy.deepcopy(template)
    tool["uid"] = next_uid()
    return tool


def apply_preset(name):
    preset = PRESETS[name]
    st.session_state["server_key"] = st.session_state.get("server_key", 0) + 1
    st.session_state["server_name_default"] = preset["server_name"]
    st.session_state["tools"] = [new_tool(tool) for tool in preset["tools"]]


def apply_selected_preset():
    apply_preset(st.session_state["preset_choice"])


def add_tool():
    st.session_state["tools"].append(new_tool(BLANK_TOOL))


def remove_last_tool():
    if len(st.session_state["tools"]) > 1:
        st.session_state["tools"].pop()


def init_state():
    if "tools" not in st.session_state:
        apply_preset(DEFAULT_PRESET)


def render_auth(default, prefix):
    auth_type = st.selectbox(
        "Authentication",
        AUTH_KEYS,
        format_func=lambda key: AUTH_LABELS[key],
        index=AUTH_KEYS.index(default["auth_type"]),
        key=f"auth_type_{prefix}",
        help="Choose how the API expects your secret. The secret itself is never typed in this app.",
    )
    auth_env = ""
    auth_name = ""
    if auth_type != "none":
        auth_env = st.text_input(
            "Environment variable that will hold the secret",
            value=default["auth_env"],
            key=f"auth_env_{prefix}",
            help="Capital letters, numbers and underscores, for example WEATHER_API_KEY",
        )
        if auth_type == "api_key_header":
            auth_name = st.text_input(
                "Header name",
                value=default["auth_name"],
                key=f"auth_name_header_{prefix}",
            )
        if auth_type == "api_key_query":
            auth_name = st.text_input(
                "Query parameter name",
                value=default["auth_name"] if default["auth_name"] != "X-API-Key" else "api_key",
                key=f"auth_name_query_{prefix}",
            )
        st.caption("You will put the real secret into a .env file after generating. Never paste it here.")
    return auth_type, auth_env, auth_name


def render_parameters(default, prefix):
    st.markdown("**Parameters** the AI can send to the API")
    table = pd.DataFrame(default["params"], columns=PARAM_COLUMNS)
    edited = st.data_editor(
        table,
        num_rows="dynamic",
        key=f"params_{prefix}",
        column_config={
            "name": st.column_config.TextColumn("Name", help="Same spelling as the API expects"),
            "type": st.column_config.SelectboxColumn("Type", options=TYPE_OPTIONS, default="string"),
            "location": st.column_config.SelectboxColumn("Sent in", options=LOCATION_OPTIONS, default="query"),
            "required": st.column_config.CheckboxColumn("Required", default=True),
            "description": st.column_config.TextColumn("Description", help="Helps the AI understand the value"),
            "example": st.column_config.TextColumn("Example", help="Used as the default value in the Test tab"),
        },
    )
    return edited.to_dict("records")


def render_tool(default):
    prefix = str(default["uid"])
    name = st.text_input(
        "Tool name",
        value=default["name"],
        key=f"name_{prefix}",
        help="Letters, numbers and underscores only, for example get_weather",
    )
    description = st.text_area(
        "What does this tool do?",
        value=default["description"],
        key=f"description_{prefix}",
        height=80,
        help="The AI reads this to decide when to use the tool. Be clear and specific.",
    )
    url_column, method_column = st.columns([4, 1])
    url = url_column.text_input("API URL", value=default["url"], key=f"url_{prefix}")
    method = method_column.selectbox(
        "Method",
        METHODS,
        index=METHODS.index(default["method"]),
        key=f"method_{prefix}",
    )
    auth_type, auth_env, auth_name = render_auth(default, prefix)
    headers_text = st.text_area(
        "Extra headers (optional, one per line as Name: value)",
        value=default["headers_text"],
        key=f"headers_{prefix}",
        height=80,
    )
    params = render_parameters(default, prefix)
    return {
        "name": name,
        "description": description,
        "url": url,
        "method": method,
        "auth_type": auth_type,
        "auth_env": auth_env,
        "auth_name": auth_name,
        "headers_text": headers_text,
        "params": params,
    }


def render_builder():
    st.subheader("Step 1: Start from an example or from scratch")
    choice_column, button_column = st.columns([3, 1])
    choice_column.selectbox("Example", list(PRESETS), key="preset_choice", label_visibility="collapsed")
    button_column.button("Load example", on_click=apply_selected_preset)
    st.caption("Loading an example replaces everything you typed below.")

    st.subheader("Step 2: Name your server")
    server_name = st.text_input(
        "Server name",
        value=st.session_state["server_name_default"],
        key=f"server_name_{st.session_state['server_key']}",
        help="Letters, numbers, hyphens and underscores. Also used as the output folder name.",
    )
    allow_private = st.checkbox(
        "Allow local and private network URLs (only for APIs running on your own computer)",
        value=False,
        key="allow_private",
    )

    st.subheader("Step 3: Describe your tools")
    tools_raw = []
    for position, default in enumerate(st.session_state["tools"], start=1):
        with st.expander(f"Tool {position}", expanded=position == 1):
            tools_raw.append(render_tool(default))

    add_column, remove_column, _ = st.columns([1, 1, 3])
    add_column.button("➕ Add tool", on_click=add_tool)
    remove_column.button("➖ Remove last", on_click=remove_last_tool)

    return server_name, allow_private, tools_raw
