
import streamlit as st


def show_guide():
    st.header("How to build your MCP server")
    st.write("Follow the sections from top to bottom. The whole process takes about five minutes.")

    with st.expander("1. What is an MCP server?", expanded=True):
        st.markdown(
            "MCP (Model Context Protocol) is a standard way for AI apps such as Claude Desktop to use outside tools. "
            "An MCP server is a small program that offers those tools.\n\n"
            "This app creates that program for you. You describe a REST API endpoint, and the generated `server.py` "
            "becomes a bridge: the AI asks for a tool, the server calls your API, and the answer goes back to the AI. "
            "Your API itself does not change."
        )

    with st.expander("2. Quick start", expanded=True):
        st.markdown(
            "1. Open the **🛠️ Build** tab and click **Load example** to start from a working setup.\n"
            "2. Give your server a name and fill in your tool details.\n"
            "3. Click **Generate MCP Server**.\n"
            "4. Open the **📦 Download** tab and download the ZIP bundle.\n"
            "5. If your API needs a secret, create a `.env` file (see section 4).\n"
            "6. Open the **🧪 Test** tab and run your tool to confirm the API answers.\n"
            "7. Connect the server to Claude Desktop (see section 6)."
        )

    with st.expander("3. What to type in each field"):
        st.markdown(
            "| Field | What to enter | Example |\n"
            "|---|---|---|\n"
            "| Server name | A short name for the whole server | `weather_server` |\n"
            "| Tool name | What the AI calls the tool. Letters, numbers, underscores | `get_weather` |\n"
            "| What does this tool do? | A clear sentence that tells the AI when to use it | `Get the current weather for a latitude and longitude` |\n"
            "| API URL | The endpoint address without secrets in it | `https://api.open-meteo.com/v1/forecast` |\n"
            "| Method | `GET` to read data, `POST` to send data | `GET` |\n"
            "| Authentication | How the API wants your secret | `Bearer token` |\n"
            "| Extra headers | Harmless headers, one per line | `Accept: application/json` |\n"
        )
        st.markdown(
            "**Parameters table**\n\n"
            "- **Name**: exactly as the API spells it, for example `latitude`.\n"
            "- **Type**: `string` (text), `integer` (whole number), `number` (decimal) or `boolean` (true or false).\n"
            "- **Sent in**: `query` puts it in the URL after the question mark, `body` puts it in the JSON body (POST only).\n"
            "- **Required**: untick it if the API works without that value.\n"
            "- **Description**: one short sentence so the AI knows what value to send.\n"
            "- **Example**: a sample value used in the Test tab.\n\n"
            "One server can hold several tools. Use **Add tool** for more endpoints."
        )

    with st.expander("4. API keys and secrets"):
        st.markdown(
            "Never type your real key into this app or into the generated code.\n\n"
            "1. In the tool, choose an **Authentication** type and an environment variable name such as `WEATHER_API_KEY`.\n"
            "2. Generate the server. The code only contains a placeholder, never the real key.\n"
            "3. Create a file named `.env` in the same folder as `server.py`:"
        )
        st.code("WEATHER_API_KEY=paste_your_real_key_here", language="bash")
        st.markdown(
            "4. Run the **🧪 Test** tab again. If a variable is missing, the tool tells you its name.\n"
            "5. Never upload `.env` to GitHub. The `.gitignore` file in this project already blocks it."
        )

    with st.expander("5. Run the generated server yourself"):
        st.markdown("Unzip the bundle, open a terminal in that folder, then run:")
        st.code(
            "python3 -m venv venv\n"
            "source venv/bin/activate\n"
            "pip install -r requirements.txt\n"
            "python server.py",
            language="bash",
        )
        st.markdown(
            "On Windows use `python` instead of `python3` and activate with `venv\\Scripts\\activate`.\n\n"
            "The server shows no output and just waits. That means it works. Press `Ctrl+C` to stop.\n\n"
            "To try your tools in a browser (needs Node.js):"
        )
        st.code("npx @modelcontextprotocol/inspector python server.py", language="bash")

    with st.expander("6. Connect to Claude Desktop"):
        st.markdown(
            "1. Open Claude Desktop, then **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json`.\n"
            "2. Copy the `mcpServers` block from the generated config file into it. If the file already has `mcpServers`, add your server next to the existing ones.\n"
            "3. Check two values: `command` must be the Python inside the virtual environment where you ran `pip install -r requirements.txt`, and `args` must be the full path to `server.py`.\n"
            "4. Fully quit Claude Desktop (not just close the window) and open it again.\n"
            "5. Start a new chat and ask something your tool can answer, for example: *What is the weather at latitude 52.52 and longitude 13.41?*\n\n"
            "Config file locations:\n\n"
            "- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`\n"
            "- Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`\n\n"
            "You can change the Python and server paths in the **📦 Download** tab before downloading the config."
        )
        st.markdown("To find your venv Python after activating it, run `which python3` (macOS and Linux) or `where python` (Windows).")

    with st.expander("7. Troubleshooting"):
        st.markdown(
            "| Problem | Fix |\n"
            "|---|---|\n"
            "| `No module named mcp.server.fastmcp` | Run `pip install \"mcp<2\"`. Version 2 renamed FastMCP. |\n"
            "| `command not found: python` on a Mac | Use `python3` and `pip` inside an activated venv. |\n"
            "| Claude Desktop does not show the tool | Check the JSON is valid, use full paths, then fully quit and reopen the app. |\n"
            "| `Missing environment variables` | Create `.env` next to `server.py` and add the variable names it lists. |\n"
            "| `HTTP 401` or `HTTP 403` | The key is wrong, expired or sent the wrong way. Check the Authentication type. |\n"
            "| `HTTP 404` | Check the API URL and the spelling of the path. |\n"
            "| `Request failed (ConnectionError)` | Check your internet connection and the host name in the URL. |\n"
            "| Parameter not accepted | Parameter names must be valid Python names. Use `user_id` instead of `user-id`. |\n"
        )

    with st.expander("8. Security checklist and limits"):
        st.markdown(
            "- Secrets live only in `.env` or environment variables. The app refuses secret-looking headers, URL passwords and secret query keys.\n"
            "- Authentication over plain `http://` is blocked. Use `https://`.\n"
            "- Local and private addresses are blocked unless you tick the box. Host names that point to private addresses through DNS are not checked.\n"
            "- Generated servers use a 30 second timeout, cut very long answers, and never print your URL or secrets in error messages.\n"
            "- The Test tab sends real requests from your computer. Run this app on your own machine only and do not host it publicly.\n"
            "- Only add tools for APIs you trust. Anything a tool returns is shown to the AI.\n"
            "- Limits: GET and POST only, no path parameters like `/posts/{id}`, and parameter names must be valid Python names."
        )
