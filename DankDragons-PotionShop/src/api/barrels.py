from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    ""
    green_ml_bought = 0
    red_ml_bought = 0
    blue_ml_bought = 0
    dark_ml_bought = 0
    spent = 0
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            spent -= (barrel.price * barrel.quantity)
            red_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[0])
            green_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[1])
            blue_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[2])
            dark_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[3])
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold) VALUES (:gold)"), {"gold": spent})
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml) 
                                              VALUES (:redML, :greenML, :blueML, :darkML)"""), 
                                          [{"redML": red_ml_bought, "greenML": green_ml_bought, "blueML": blue_ml_bought, "darkML": dark_ml_bought}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # med $250 -2500ml
    # sm $100 -500ml
    # mini $60 -200ml
    purchase = []
    capacity = 1000
    print(wholesale_catalog)
    with db.engine.begin() as conn:
        low_potion = conn.execute(sqlalchemy.text("SELECT potion_sku FROM potion_ledger ORDER BY SUM(change) ASC LIMIT 1")).scalar_one()
        low_inventory = conn.execute(sqlalchemy.text("""
                                        SELECT SUM(change)
                                        FROM potion_ledger 
                                        WHERE potion_sku = :low_potion"""),{"low_potion": low_potion}).scalar()
        red_needed, green_needed, blue_needed, dark_needed = conn.execute(sqlalchemy.text("""
                                                        SELECT red_ml, green_ml, blue_ml, dark_ml 
                                                        FROM potions WHERE name = :potion"""), [{"potion": low_potion}]).scalar()
        wallet = conn.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledger")).scalar()
        level = conn.execute(sqlalchemy.text("SELECT SUM(red_ml + green_ml + blue_ml + dark_ml) FROM ml_ledger")).scalar()
    #traverse catalog
    for barrel in wholesale_catalog:
        if((red_needed > 0 or green_needed > 0 or blue_needed > 0 or dark_needed > 0) and level < capacity):
            # if DARK barrel in catalog
            if barrel.potion_type == [0, 0, 0, 1] and dark_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                level += barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
            # if GREEN barrel in catalog
            elif barrel.potion_type == [0,1, 0, 0] and green_needed > 0 and barrel.quantity and barrel.price < wallet: 
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                level += barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
            # if RED barrel in catalog
            elif (barrel.potion_type == [1, 0, 0, 0]) and red_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                level += barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
            # if BLUE barrel in catalog
            elif barrel.potion_type == [0, 0, 1, 0] and blue_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                level += barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })

    return purchase
