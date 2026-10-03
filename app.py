from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes.auth_routes import router as auth_router
from routes.food_routes import router as food_router
from routes.diary_routes import router as diary_router
from routes.weight_routes import router as weight_router
from routes.scanner_routes import router as scanner_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NWFP - Nutrition & Wellness Fitness Pal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(food_router)
app.include_router(diary_router)
app.include_router(weight_router)
app.include_router(scanner_router)


@app.get("/")
def root():
    return {"message": "NWFP API", "version": "1.0.0", "docs": "/docs"}
