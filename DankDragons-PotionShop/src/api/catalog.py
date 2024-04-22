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
        inventory = conn.execute(sqlalchemy.text("SELECT * FROM potions"))
        for sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml in inventory:
            if quantity != 0:
                catalog.append({
                    "sku": sku,
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "potion_type": [red_ml, green_ml, blue_ml, dark_ml]
                })
    return catalog
