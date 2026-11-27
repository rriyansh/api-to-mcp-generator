import streamlit as st

from src.generator import generate_files
from src.parser import ParserError, parse_input

st.set_page_config(page_title="API to MCP Generator", page_icon="🔌")

st.title("API to MCP Generator")
st.write("Enter your REST API details and generate a ready-to-run MCP server.")

tool_name = st.text_input("Tool name", value="get_posts")
description = st.text_area(
    "Tool description",
    value="Fetch posts from JSONPlaceholder, optionally filtered by user id.",
)
api_url = st.text_input("API URL", value="https://jsonplaceholder.typicode.com/posts")
http_method = st.selectbox("HTTP method", ["GET", "POST"])
headers_text = st.text_area(
    "Headers (one per line, format: Name: value)",
    value="Accept: application/json",
    help="For secrets use a placeholder, for example: Authorization: Bearer ${API_TOKEN}",
)
parameters_text = st.text_area(
    "Parameters (one per line, format: name, type, location, required)",
    value="userId, integer, query, no",
    help="type: string, integer, number, boolean. location: query or body. required: yes or no.",
)

if st.button("Generate MCP Server"):
    try:
        data = parse_input(
            tool_name,
            description,
            api_url,
            http_method,
            headers_text,
            parameters_text,
        )
        st.session_state["result"] = generate_files(data)
        st.session_state["env_vars"] = data["env_vars"]
    except ParserError as error:
        st.session_state.pop("result", None)
        st.error(str(error))

if "result" in st.session_state:
    result = st.session_state["result"]
    st.success("MCP server generated successfully.")

    if st.session_state["env_vars"]:
        names = ", ".join(st.session_state["env_vars"])
        st.info(
            f"Create a file named .env next to the generated server and set these values: {names}"
        )

    st.subheader("Generated server")
    st.code(result["server_code"], language="python")

    st.subheader("Claude Desktop config")
    st.code(result["config_text"], language="json")

    st.download_button(
        label="Download generated_mcp_server.py",
        data=result["server_code"],
        file_name="generated_mcp_server.py",
        mime="text/x-python",
    )
    st.download_button(
        label="Download claude_desktop_config.json",
        data=result["config_text"],
        file_name="claude_desktop_config.json",
        mime="application/json",
    )
