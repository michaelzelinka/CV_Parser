from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="CV Parser API",
    version="0.2.0",
    description="Internal API for CV parsing and matching"
)

# ✅ CORS – nutné pro Streamlit → Render komunikaci
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # můžeš později omezit na konkrétní doménu
    allow_credentials=True,
    allow_methods=["*"],          # povolit POST, GET, OPTIONS
    allow_headers=["*"],
)

# ✅ Router – bez prefixu, endpoint je /parse
app.include_router(router)

# ✅ Base endpoints
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
