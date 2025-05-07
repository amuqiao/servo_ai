from fastapi import FastAPI
from src.middlewares.logging_middleware import logging_middleware

app = FastAPI(title="Servo AI API")
app.middleware('http')(logging_middleware)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)