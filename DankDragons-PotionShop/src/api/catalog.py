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
    with db.engine.begin() as conn:
        my_inventory = conn.execute(sqlalchemy.text("SELECT sku, name, inventory, price, red_ml, green_ml, blue_ml, dark_ml FROM potions"))
        for sku, name, inventory, price, red_ml, green_ml, blue_ml, dark_ml in my_inventory:
            if inventory != 0:
                catalog.append({
                    "sku": sku,
                    "name": name,
                    "quantity": inventory,
                    "price": price,
                    "potion_type": [red_ml, green_ml, blue_ml, dark_ml]
                })
    return catalog
