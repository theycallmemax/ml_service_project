from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.database.database import engine, Base
from app.models import models
from app.models.update_models import update_models

# u0421u043eu0437u0434u0430u0435u043c u0442u0430u0431u043bu0438u0446u044b u0432 u0411u0414
Base.metadata.create_all(bind=engine)

# u0421u043eu0437u0434u0430u0435u043c u044du043au0437u0435u043cu043fu043bu044fu0440 u043fu0440u0438u043bu043eu0436u0435u043du0438u044f FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# u041du0430u0441u0442u0440u0430u0438u0432u0430u0435u043c CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # u0412 u043fu0440u043eu0434u0430u043au0448u0435u043du0435 u043du0443u0436u043du043e u043eu0433u0440u0430u043du0438u0447u0438u0442u044c u0434u043eu043cu0435u043du044b
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# u041fu043eu0434u043au043bu044eu0447u0430u0435u043c u043cu0430u0440u0448u0440u0443u0442u044b API
app.include_router(api_router, prefix=settings.API_V1_STR)

# u041eu0431u043du043eu0432u043bu044fu0435u043c u043cu043eu0434u0435u043bu0438 u0432 u0431u0430u0437u0435 u0434u0430u043du043du044bu0445 u043fu0440u0438 u0437u0430u043fu0443u0441u043au0435
update_models()

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# u0414u043eu0431u0430u0432u0438u043c u043au043eu0440u043du0435u0432u043eu0439 u043cu0430u0440u0448u0440u0443u0442 u0434u043bu044f u043fu0440u043eu0432u0435u0440u043au0438 u0437u0434u043eu0440u043eu0432u044cu044f u0441u0435u0440u0432u0435u0440u0430
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
