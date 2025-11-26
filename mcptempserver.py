# temp_mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="TemperatureServer",
    host="0.0.0.0",
    port=8000,
    stateless_http=True, 
    json_response=True
)

@mcp.tool()
def c_to_f(celsius: float) -> float:
    return celsius * 9/5 + 32

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
