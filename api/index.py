from fastapi import FastAPI

app = FastAPI(title="tee-es-t API", version="1.0.0")


@app.get("/api")
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "tee-es-t"}
