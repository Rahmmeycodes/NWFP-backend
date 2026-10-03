"""Run once to populate the food database with common foods."""
from database import SessionLocal, engine, Base
from models import Food

Base.metadata.create_all(bind=engine)

FOODS = [
    ("Chicken Breast (grilled)", "Generic", "100g", 165, 31, 0, 3.6, 0, 0, 74),
    ("Brown Rice (cooked)", "Generic", "100g", 123, 2.7, 25.6, 1, 1.8, 0.4, 1),
    ("Egg (large, whole)", "Generic", "1 egg (50g)", 72, 6.3, 0.4, 4.8, 0, 0.2, 71),
    ("Banana", "Generic", "1 medium (118g)", 105, 1.3, 27, 0.4, 3.1, 14.4, 1),
    ("Apple", "Generic", "1 medium (182g)", 95, 0.5, 25.1, 0.3, 4.4, 18.9, 2),
    ("Salmon (baked)", "Generic", "100g", 208, 20.4, 0, 13.4, 0, 0, 59),
    ("Sweet Potato (baked)", "Generic", "100g", 90, 2, 20.7, 0.1, 3.3, 6.5, 36),
    ("Broccoli (steamed)", "Generic", "100g", 35, 2.4, 7.2, 0.4, 3.3, 1.4, 41),
    ("Oatmeal (cooked)", "Generic", "1 cup (234g)", 154, 5.4, 27.4, 2.6, 4, 0.6, 2),
    ("Greek Yogurt (plain, nonfat)", "Generic", "170g", 100, 17, 6, 0.7, 0, 5.5, 56),
    ("Almonds", "Generic", "28g (1oz)", 164, 6, 6, 14.2, 3.5, 1.2, 0),
    ("Avocado", "Generic", "1 medium (150g)", 240, 3, 12.8, 22, 10, 1, 11),
    ("White Rice (cooked)", "Generic", "100g", 130, 2.7, 28.2, 0.3, 0.4, 0, 1),
    ("Whole Wheat Bread", "Generic", "1 slice (28g)", 69, 3.6, 11.6, 1.2, 1.9, 1.4, 132),
    ("Peanut Butter", "Generic", "2 tbsp (32g)", 188, 8, 6, 16, 2, 3, 136),
    ("Milk (whole)", "Generic", "1 cup (244ml)", 149, 8, 12, 8, 0, 12, 105),
    ("Milk (skim)", "Generic", "1 cup (244ml)", 83, 8.3, 12.2, 0.2, 0, 12.5, 103),
    ("Cheddar Cheese", "Generic", "28g (1oz)", 113, 7, 0.4, 9.3, 0, 0.1, 174),
    ("Pasta (cooked)", "Generic", "100g", 131, 5, 25, 1.1, 1.8, 0.6, 1),
    ("Ground Beef (90% lean)", "Generic", "100g", 176, 20, 0, 10, 0, 0, 66),
    ("Tuna (canned in water)", "Generic", "100g", 116, 25.5, 0, 0.8, 0, 0, 338),
    ("Spinach (raw)", "Generic", "100g", 23, 2.9, 3.6, 0.4, 2.2, 0.4, 79),
    ("Cottage Cheese (low-fat)", "Generic", "100g", 72, 12.4, 2.7, 1, 0, 2.7, 406),
    ("Quinoa (cooked)", "Generic", "100g", 120, 4.4, 21.3, 1.9, 2.8, 0.9, 7),
    ("Lentils (cooked)", "Generic", "100g", 116, 9, 20.1, 0.4, 7.9, 1.8, 2),
    ("Olive Oil", "Generic", "1 tbsp (14ml)", 119, 0, 0, 13.5, 0, 0, 0),
    ("Honey", "Generic", "1 tbsp (21g)", 64, 0.1, 17.3, 0, 0, 17.2, 1),
    ("Protein Powder (whey)", "Generic", "1 scoop (30g)", 120, 24, 3, 1.5, 0, 1, 130),
    ("Tortilla (flour)", "Generic", "1 medium (45g)", 140, 3.6, 23.6, 3.5, 1.3, 1, 331),
    ("Black Beans (cooked)", "Generic", "100g", 132, 8.9, 23.7, 0.5, 8.7, 0.3, 1),
]

def seed():
    db = SessionLocal()
    if db.query(Food).count() > 0:
        print("Foods already seeded.")
        db.close()
        return
    for name, brand, serving, cal, pro, carb, fat, fiber, sugar, sodium in FOODS:
        db.add(Food(
            name=name, brand=brand, serving_size=serving,
            calories=cal, protein=pro, carbs=carb, fat=fat,
            fiber=fiber, sugar=sugar, sodium=sodium,
        ))
    db.commit()
    print(f"Seeded {len(FOODS)} foods.")
    db.close()

if __name__ == "__main__":
    seed()
