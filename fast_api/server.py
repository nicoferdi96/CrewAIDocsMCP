import contextlib
import os

from crewai_docs_server import mcp as crewai_docs
from fastapi import FastAPI

# from tavily_server import mcp as tavily_search


# Create a combined lifespan to manage all session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # await stack.enter_async_context(tavily_search.session_manager.run())
        await stack.enter_async_context(crewai_docs.session_manager.run())
        yield


app = FastAPI(lifespan=lifespan)

# Mount all MCP servers
# app.mount("/tavily", tavily_search.streamable_http_app())
app.mount("/crewai", crewai_docs.streamable_http_app())


# Add a root endpoint to show available servers
@app.get("/")
def read_root():
    return {
        "message": "MCP Multi-Server Gateway",
        "servers": {
            # "tavily": "/tavily/mcp/",
            "crewai": "/crewai/mcp/",
        },
    }


PORT = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
