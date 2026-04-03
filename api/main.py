from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="CV Parser API")

app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
