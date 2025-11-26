from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()


def c_to_f(celsius: float) -> float:
    return celsius * 9/5 + 32


async def get_tokyo_weather() -> dict:
    """get tokyo weather information from Open-Meteo API"""
    try:
        async with httpx.AsyncClient() as client:
            # 使用 Open-Meteo 免费 API（无需密钥）
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "current": "temperature_2m,weather_code,wind_speed_10m",
                    "timezone": "Asia/Tokyo"
                }
            )
            data = resp.json()
            current = data.get("current", {})
            return {
                "temperature": current.get("temperature_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "weather_code": current.get("weather_code"),
                "timezone": data.get("timezone")
            }
    except Exception as e:
        return {"error": str(e)}


def get_hobby(hobby_type: str = "reading") -> dict:
    """get user hobby information based on hobby type"""
    hobby_info = {
        "reading": {"name": "reading", "description": "Love reading books like the Bible and articles", "frequency": "daily"},
        "writing": {"name": "writing", "description": "Enjoy creative writing and blogging", "frequency": "weekly"},
        "coding": {"name": "coding", "description": "Passionate about programming and software development", "frequency": "daily"},
    }
    return hobby_info.get(hobby_type, {"name": hobby_type, "description": "Hobby information not available", "frequency": "unknown"})


@app.get("/mcp")
async def mcp_get():
    return {"status": "MCP server OK. Use POST for JSON-RPC."}


@app.options("/mcp")
async def mcp_options():
    return JSONResponse(status_code=200, content={})


@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()
    print("RAW BODY:", body)

    method = body.get("method")
    jsonrpc = body.get("jsonrpc", "2.0")
    req_id = body.get("id")
    params = body.get("params") or {}

    # 0) notification：没有 id，一律忽略，返回 200 空
    # 例如：notifications/initialized
    if req_id is None:
        print(f"[MCP] Notification received: {method}, ignoring")
        return JSONResponse(status_code=200, content={})

    # 1) initialize -------------------------------------------------
    if method == "initialize":
        protocol_version = params.get("protocolVersion", "2025-06-18")
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "Weather and Hobby Information Server",
                    "version": "0.2.0",
                    "description": "A server providing tools for temperature conversion, Tokyo weather data, and personal hobby information",
                    "tools": [
                        {
                            "name": "c_to_f",
                            "description": "Convert temperature from Celsius to Fahrenheit"
                        },
                        {
                            "name": "get_tokyo_weather",
                            "description": "Fetch real-time weather data for Tokyo, Japan"
                        },
                        {
                            "name": "get_hobby",
                            "description": "Retrieve user hobby information"
                        }
                    ]
                },
            },
        }

    # 2) tools/list -------------------------------------------------
    if method == "tools/list":
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "c_to_f",
                        "description": "Convert temperature from Celsius to Fahrenheit. Takes a temperature value in Celsius and returns the equivalent Fahrenheit value. Useful for temperature conversions and weather-related calculations.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "celsius": {"type": "number", "description": "Temperature value in Celsius degrees"}
                            },
                            "required": ["celsius"],
                        },
                    },
                    {
                        "name": "get_tokyo_weather",
                        "description": "Fetch real-time weather data for Tokyo, Japan. Returns current temperature in Celsius, wind speed in km/h, weather code, and timezone information. This tool requires no parameters and uses the Open-Meteo free weather API.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    {
                        "name": "get_hobby",
                        "description": "Retrieve user hobby information based on hobby type. Returns details about a specific hobby including description and frequency.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hobby_type": {"type": "string", "description": "The type of hobby (e.g., 'reading', 'writing', 'coding')"}
                            },
                            "required": ["hobby_type"],
                        },
                    }
                ]
            },
        }

    # 3) tools/call -------------------------------------------------
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}

        if tool_name == "c_to_f":
            c = arguments.get("celsius")
            result = c_to_f(c)
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{c}°C = {result}°F",
                        }
                    ]
                },
            }

        if tool_name == "get_tokyo_weather":
            weather = await get_tokyo_weather()
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tokyo Weather: {weather.get('temperature')}°C, Wind: {weather.get('wind_speed')} km/h",
                        }
                    ]
                },
            }

        if tool_name == "get_hobby":
            hobby_type = arguments.get("hobby_type", "reading")
            hobby = get_hobby(hobby_type)
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Hobby: {hobby['name']}, Description: {hobby['description']}, Frequency: {hobby['frequency']}",
                        }
                    ]
                },
            }

        # 未知工具：用 JSON-RPC error，但 HTTP 仍 200
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "error": {
                "code": -32000,
                "message": f"Unknown tool: {tool_name}",
            },
        }

    # 4) 未知 method：返回 JSON-RPC error，HTTP 200 ----------------
    return {
        "jsonrpc": jsonrpc,
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }
