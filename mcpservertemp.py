from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.types import (
    ListToolsRequest,
    ListToolsResult,
    CallToolRequest,
    CallToolResult,
    TextContent,
)
import json

app = FastAPI()

# ---- 定义工具（你可以增加更多工具） ----  this file not good for mcp protocol

def c_to_f(celsius: float):
    return celsius * 9/5 + 32


# ---- MCP /mcp endpoint ----

@app.post("/mcp")
async def mcp_endpoint(request: Request):

    raw_body = await request.body()
    body = json.loads(raw_body.decode("utf-8"))

    mcp_type = body.get("type")

    # ================
    # 1) 列出工具
    # ================
    if mcp_type == "list_tools":
        print("[MCP] ListToolsRequest received")

        return JSONResponse(
            ListToolsResult(
                tools=[
                    {
                        "name": "c_to_f",
                        "description": "Convert Celsius to Fahrenheit",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "celsius": {"type": "number"}
                            },
                            "required": ["celsius"]
                        },
                    }
                ]
            ).model_dump()
        )

    # =====================
    # 2) 调用工具 (CallTool)
    # =====================
    elif mcp_type == "call_tool":
        print("[MCP] CallToolRequest received")

        req = CallToolRequest.model_validate(body)

        if req.name == "c_to_f":
            c = req.arguments.get("celsius")
            result = c_to_f(c)

            return JSONResponse(
                CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=str(result)
                        )
                    ]
                ).model_dump()
            )

    # 其他未知类型
    return JSONResponse({"error": "Unknown MCP request"}, status_code=400)
