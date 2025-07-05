import contextlib
import os

from fastapi import FastAPI
from tavily_server import mcp as tevily_search

# from another_server import mcp as another_mcp_name


# Create a combined lifespan to manage both session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(tevily_search.session_manager.run())
        # await stack.enter_async_context(another_mcp_name.session_manager.run())
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/tevily_search", tevily_search.streamable_http_app())
# app.mount("/another_mcp_name", tevily_search.streamable_http_app())

PORT = os.environ.get("PORT", 10000)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
