from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    green_bottles = 0
    with db.engine.begin() as connection:
        green_bottles = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        if green_bottles >= 1:
            green_bottles = 1
    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": "{green_bottles}",
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
