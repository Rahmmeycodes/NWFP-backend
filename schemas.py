from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    calorie_goal: int
    protein_goal: float
    carbs_goal: float
    fat_goal: float
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class GoalsUpdate(BaseModel):
    calorie_goal: Optional[int] = None
    protein_goal: Optional[float] = None
    carbs_goal: Optional[float] = None
    fat_goal: Optional[float] = None


class FoodCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    serving_size: str = "100g"
    calories: float
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0


class FoodResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    serving_size: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    sugar: float
    sodium: float

    model_config = {"from_attributes": True}


class DiaryEntryCreate(BaseModel):
    food_id: int
    date: date
    meal_type: str
    servings: float = 1.0


class DiaryEntryResponse(BaseModel):
    id: int
    food: FoodResponse
    date: date
    meal_type: str
    servings: float
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float

    model_config = {"from_attributes": True}


class DailySummary(BaseModel):
    date: date
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    calorie_goal: int
    protein_goal: float
    carbs_goal: float
    fat_goal: float
    calories_remaining: float
    meals: dict[str, list[DiaryEntryResponse]]


class WeightLogCreate(BaseModel):
    weight: float
    date: date


class WeightLogResponse(BaseModel):
    id: int
    weight: float
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}
