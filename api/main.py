from fastapi import FastAPI
from api.routes import router
app = FastAPI(title="CV Parser API")
app.include_router(router)
@app.get("/health")
def health():    
  return {"status": "ok"}


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running"}
