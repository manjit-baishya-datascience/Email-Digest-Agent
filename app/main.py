import asyncio
import logging
from fastapi import FastAPI, HTTPException
from app.logging_config import setup_logging
from app.graph import build_graph

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Email Digest Agent")

# Compile the graph once at startup, reuse across requests
compiled_graph = build_graph()

@app.post("/trigger")
async def trigger_run():
    logger.info("Received trigger request — starting pipeline run")

    # Camoufox's sync API can't run inside FastAPI's asyncio event loop
    # directly, so the blocking pipeline is offloaded to a thread.
    result = await asyncio.to_thread(compiled_graph.invoke, {})

    if result.get("error"):
        logger.error(f"Pipeline failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])

    logger.info(f"Pipeline succeeded — digest saved to {result['output_path']}")
    return {
        "status": "success",
        "output_path": result["output_path"],
        "email_count": len(result.get("emails", [])),
        "digest_item_count": len(result.get("digest_items", [])),
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}