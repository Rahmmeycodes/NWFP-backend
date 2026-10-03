from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes.auth_routes import router as auth_router
from routes.food_routes import router as food_router
from routes.diary_routes import router as diary_router
from routes.weight_routes import router as weight_router
from routes.scanner_routes import router as scanner_router
from routes.image_scanner_routes import router as image_scanner_router
from routes.exercise_routes import router as exercise_router
from routes.profile_routes import router as profile_router
from routes.progress_routes import router as progress_router
from routes.water_routes import router as water_router
from routes.saved_meals_routes import router as saved_meals_router

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
app.include_router(image_scanner_router)
app.include_router(exercise_router)
app.include_router(profile_router)
app.include_router(progress_router)
app.include_router(water_router)
app.include_router(saved_meals_router)


@app.get("/")
def root():
    return {"message": "NWFP API", "version": "1.0.0", "docs": "/docs"}
