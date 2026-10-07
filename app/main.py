from fastapi import FastAPI

app = FastAPI(title="Uptime Monitor")


@app.get("/health")
def health():
    return {"status": "ok"}