from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        green_bottles = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        red_bottles = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        blue_bottles = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        if green_bottles > 0:
            catalog.append({
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity":1,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            })
        if red_bottles > 0:
            catalog.append({
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity":1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            })
        if blue_bottles > 0:
            catalog.append({
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity":1,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            })
    return catalog
