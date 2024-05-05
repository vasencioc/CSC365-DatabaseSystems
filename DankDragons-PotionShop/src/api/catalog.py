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
        my_inventory = conn.execute(sqlalchemy.text("""
                    SELECT potion_sku, name, red_ml, green_ml, blue_ml, dark_ml, price, SUM(change) as stock
                    FROM potions
                    JOIN potion_ledger ON potion_ledger.potion_sku = potions.sku
                    GROUP BY potion_sku, name, red_ml, green_ml, blue_ml, dark_ml, price
                    """))
        for potion_sku, name, red_ml, green_ml, blue_ml, dark_ml, price, stock in my_inventory:
            if stock != 0:
                catalog.append({
                    "sku": potion_sku,
                    "name": name,
                    "quantity": stock,
                    "price": price,
                    "potion_type": [red_ml, green_ml, blue_ml, dark_ml]
                })
    return catalog
