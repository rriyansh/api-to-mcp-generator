
BLANK_TOOL = {
    "name": "",
    "description": "",
    "url": "https://",
    "method": "GET",
    "auth_type": "none",
    "auth_env": "API_TOKEN",
    "auth_name": "X-API-Key",
    "headers_text": "Accept: application/json",
    "params": [],
}

JSONPLACEHOLDER_SERVER = {
    "server_name": "jsonplaceholder_server",
    "tools": [
        {
            "name": "get_posts",
            "description": "Fetch blog posts from JSONPlaceholder. Optionally filter by the id of the user who wrote them.",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "method": "GET",
            "auth_type": "none",
            "auth_env": "API_TOKEN",
            "auth_name": "X-API-Key",
            "headers_text": "Accept: application/json",
            "params": [
                {
                    "name": "userId",
                    "type": "integer",
                    "location": "query",
                    "required": False,
                    "description": "Only return posts written by this user id",
                    "example": "1",
                }
            ],
        },
        {
            "name": "create_post",
            "description": "Create a new fake blog post on JSONPlaceholder. Nothing is really saved.",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "method": "POST",
            "auth_type": "none",
            "auth_env": "API_TOKEN",
            "auth_name": "X-API-Key",
            "headers_text": "Accept: application/json",
            "params": [
                {
                    "name": "title",
                    "type": "string",
                    "location": "body",
                    "required": True,
                    "description": "Title of the post",
                    "example": "Hello MCP",
                },
                {
                    "name": "body",
                    "type": "string",
                    "location": "body",
                    "required": True,
                    "description": "Text content of the post",
                    "example": "My first post created through an MCP server",
                },
                {
                    "name": "userId",
                    "type": "integer",
                    "location": "body",
                    "required": True,
                    "description": "Id of the author",
                    "example": "1",
                },
            ],
        },
    ],
}

WEATHER_SERVER = {
    "server_name": "weather_server",
    "tools": [
        {
            "name": "get_weather",
            "description": "Get the current weather for a place using its latitude and longitude (Open-Meteo).",
            "url": "https://api.open-meteo.com/v1/forecast",
            "method": "GET",
            "auth_type": "none",
            "auth_env": "API_TOKEN",
            "auth_name": "X-API-Key",
            "headers_text": "Accept: application/json",
            "params": [
                {
                    "name": "latitude",
                    "type": "number",
                    "location": "query",
                    "required": True,
                    "description": "Latitude of the place, for example 52.52",
                    "example": "52.52",
                },
                {
                    "name": "longitude",
                    "type": "number",
                    "location": "query",
                    "required": True,
                    "description": "Longitude of the place, for example 13.41",
                    "example": "13.41",
                },
                {
                    "name": "current_weather",
                    "type": "string",
                    "location": "query",
                    "required": False,
                    "description": "Send the text true to include current weather",
                    "example": "true",
                },
            ],
        }
    ],
}

BLANK_SERVER = {
    "server_name": "my_api_server",
    "tools": [BLANK_TOOL],
}

PRESETS = {
    "JSONPlaceholder (GET and POST)": JSONPLACEHOLDER_SERVER,
    "Open-Meteo weather (GET)": WEATHER_SERVER,
    "Blank tool": BLANK_SERVER,
}
