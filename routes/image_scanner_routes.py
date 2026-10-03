import os
import json
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import anthropic

from models import User
from auth import get_current_user

router = APIRouter(prefix="/api/scanner/image", tags=["image-scanner"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

ANALYSIS_PROMPT = """Analyze this food image. Identify every food item visible and estimate the nutritional content per item.

Return ONLY valid JSON in this exact format, no other text:
{
  "foods": [
    {
      "name": "food name",
      "estimated_portion": "e.g. 1 cup, 200g, 1 medium",
      "calories": 0,
      "protein": 0,
      "carbs": 0,
      "fat": 0,
      "fiber": 0,
      "sugar": 0
    }
  ],
  "total_calories": 0,
  "meal_description": "Brief description of the meal"
}

Be as accurate as possible with portion sizes based on visual cues (plate size, utensils, etc). All macro values should be in grams. Calories in kcal."""


class FoodItem(BaseModel):
    name: str
    estimated_portion: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float = 0
    sugar: float = 0


class ImageAnalysisResponse(BaseModel):
    foods: list[FoodItem]
    total_calories: float
    meal_description: str


@router.post("", response_model=ImageAnalysisResponse)
async def analyze_food_image(
    image: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    content_type = image.content_type or "image/jpeg"
    if content_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise HTTPException(status_code=400, detail="Unsupported image format. Use JPEG, PNG, GIF, or WebP.")

    image_bytes = await image.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 20MB.")

    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": content_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": ANALYSIS_PROMPT},
            ],
        }],
    )

    response_text = next(
        (block.text for block in response.content if block.type == "text"), ""
    )

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response_text[start:end])
        else:
            raise HTTPException(status_code=502, detail="Failed to parse nutrition analysis")

    return ImageAnalysisResponse(**result)
