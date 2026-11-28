import json

import streamlit as st

from src.builder import init_state, render_builder
from src.generator import build_config, generate_files, sample_arguments
from src.guide import show_guide
from src.parser import ParserError, parse_server
from src.tester import run_tool

st.set_page_config(page_title="API to MCP Generator", page_icon="🔌", layout="wide")

init_state()


def language_for(file_name):
    if file_name.endswith(".py"):
        return "python"
    if file_name.endswith(".json"):
        return "json"
    if file_name.endswith(".md"):
        return "markdown"
    if file_name.endswith(".example"):
        return "bash"
    return "text"


def show_sidebar():
    st.sidebar.title("🔌 API to MCP Generator")
    st.sidebar.caption("Version 2")
    st.sidebar.markdown(
        "**Workflow**\n\n"
        "1. 📘 Read the guide\n"
        "2. 🛠️ Build your tools\n"
        "3. 📦 Download the bundle\n"
        "4. 🧪 Test your tool"
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        "**Security reminders**\n\n"
        "- Never type real keys here\n"
        "- Keep secrets in a `.env` file\n"
        "- Run this app on your own computer only"
    )


def handle_generate(server_name, allow_private, tools_raw):
    try:
        data = parse_server(server_name, tools_raw, allow_private)
        result = generate_files(data)
    except ParserError as error:
        st.error(str(error))
        return
    st.session_state["parsed"] = data
    st.session_state["result"] = result
    st.session_state["generation"] = st.session_state.get("generation", 0) + 1
    st.success("Your MCP server is ready. Open the 📦 Download tab next.")


def show_build_tab():
    server_name, allow_private, tools_raw = render_builder()
    st.subheader("Step 4: Generate")
    if st.button("🚀 Generate MCP Server", type="primary"):
        handle_generate(server_name, allow_private, tools_raw)


def show_config_editor(data, result):
    generation = st.session_state["generation"]
    with st.expander("Customize claude_desktop_config.json"):
        st.caption(
            "Use the full path of server.py on the computer where Claude Desktop runs, "
            "and the Python from the virtual environment that has the requirements installed."
        )
        server_path = st.text_input(
            "Full path to server.py",
            value=result["server_path"],
            key=f"config_server_path_{generation}",
        )
        python_command = st.text_input(
            "Python command",
            value=result["python_command"],
            key=f"config_python_{generation}",
        )
        config_text = build_config(data["server_name"], server_path, python_command)
        st.code(config_text, language="json")
        st.download_button(
            "Download claude_desktop_config.json",
            data=config_text,
            file_name="claude_desktop_config.json",
            mime="application/json",
            key=f"download_config_{generation}",
        )


def show_download_tab():
    result = st.session_state.get("result")
    data = st.session_state.get("parsed")
    if result is None:
        st.info("Generate a server in the 🛠️ Build tab first.")
        return

    st.success(f"Server '{data['server_name']}' is ready with {len(data['tools'])} tool(s).")
    for warning in data["warnings"]:
        st.warning(warning)

    st.download_button(
        "⬇️ Download everything (ZIP)",
        data=result["zip_bytes"],
        file_name=f"{data['server_name']}.zip",
        mime="application/zip",
        type="primary",
    )
    st.caption(f"The files are also saved on this computer in: {result['folder']}")

    if data["env_vars"]:
        names = ", ".join(data["env_vars"])
        st.info(
            f"This server needs these secrets: {names}. "
            "Create a file named .env next to server.py and add one line per variable, for example NAME=your_value."
        )

    file_names = list(result["files"])
    tabs = st.tabs(file_names)
    for tab, file_name in zip(tabs, file_names):
        with tab:
            st.code(result["files"][file_name], language=language_for(file_name))
            st.download_button(
                f"Download {file_name}",
                data=result["files"][file_name],
                file_name=file_name,
                mime="text/plain",
                key=f"download_{file_name}_{st.session_state['generation']}",
            )

    show_config_editor(data, result)


def show_test_tab():
    result = st.session_state.get("result")
    data = st.session_state.get("parsed")
    if result is None:
        st.info("Generate a server in the 🛠️ Build tab first.")
        return

    generation = st.session_state["generation"]
    st.write("Run one of your tools to check that the API answers. This sends a real request from your computer.")
    if data["env_vars"]:
        names = ", ".join(data["env_vars"])
        st.info(f"Add these to {result['folder']}/.env before testing: {names}")

    tool_names = [tool["name"] for tool in data["tools"]]
    chosen = st.selectbox("Tool to test", tool_names, key=f"test_tool_{generation}")
    tool = next(item for item in data["tools"] if item["name"] == chosen)
    arguments_text = st.text_area(
        "Arguments (JSON)",
        value=json.dumps(sample_arguments(tool), indent=2),
        height=180,
        key=f"test_arguments_{generation}_{chosen}",
    )
    if st.button("▶️ Run tool", type="primary"):
        with st.spinner("Calling the API..."):
            success, output = run_tool(result["server_path"], chosen, arguments_text)
        if not success:
            st.error(output)
            return
        try:
            st.json(json.loads(output))
        except (json.JSONDecodeError, TypeError):
            st.code(output)


show_sidebar()

st.title("API to MCP Generator")
st.write("Turn a REST API endpoint into a ready-to-run MCP server in a few clicks.")

guide_tab, build_tab, download_tab, test_tab = st.tabs(["📘 Guide", "🛠️ Build", "📦 Download", "🧪 Test"])

with guide_tab:
    show_guide()

with build_tab:
    show_build_tab()

with download_tab:
    show_download_tab()

with test_tab:
    show_test_tab()
