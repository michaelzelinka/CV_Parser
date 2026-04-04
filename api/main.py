from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="CV Parser API",
    version="0.2.0",
    description="Internal API for CV parsing and matching"
)

# Register router
app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
