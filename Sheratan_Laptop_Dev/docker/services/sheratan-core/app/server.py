import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

APP = FastAPI(title="Sheratan Core (Tower)", version="0.1.0")

LLM_BASE_URL = os.getenv("SHERATAN_LLM_BASE_URL", "http://llm-bridge:3000/api/llm/call")
UVICORN_WORKERS = int(os.getenv("UVICORN_WORKERS", "1"))

class LLMCall(BaseModel):
    payload: dict

@APP.get("/health")
def health():
    return {"ok": True, "service": "sheratan-core", "llm_base_url": LLM_BASE_URL}

@APP.post("/llm/ping")
async def llm_ping(call: LLMCall):
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(LLM_BASE_URL, json=call.payload)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"llm_unreachable: {e}")
    ct = r.headers.get("content-type","")
    return {"ok": True, "status": r.status_code, "data": r.json() if "application/json" in ct else r.text}

def main():
    import uvicorn
    uvicorn.run("app.server:APP", host="0.0.0.0", port=8000, workers=UVICORN_WORKERS)

if __name__ == "__main__":
    main()
