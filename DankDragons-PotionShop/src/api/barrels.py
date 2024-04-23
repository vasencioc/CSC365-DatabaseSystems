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
    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        if barrel.potion_type == [0, 1, 0, 0]:
            green_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [1, 0, 0, 0]:
            red_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0, 0, 1, 0]:
            blue_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0, 0, 0, 1]:
            dark_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        else:
            raise Exception("Invalid Barrel Type")
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET gold = gold - :spent, num_green_ml = num_green_ml + :green_ml_bought, num_red_ml = num_red_ml + :red_ml_bought, num_blue_ml = num_blue_ml + :blue_ml_bought, num_dark_ml = num_dark_ml + :dark_ml_bought"),
            [{"spent": spent, "green_ml_bought": green_ml_bought, "red_ml_bought": red_ml_bought, "blue_ml_bought": blue_ml_bought, "dark_ml_bought": dark_ml_bought}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    purchase = []
    print(wholesale_catalog)
    with db.engine.begin() as conn:
        low_potion = conn.execute(sqlalchemy.text("SELECT name FROM potions ORDER BY quantity ASC LIMIT 1"))
        potions_needed = conn.execute(sqlalchemy.text("SELECT SUM(inventory)FROM potions")).scalar() - 50
        if(potions_needed != 0):
            red_needed = conn.execute(sqlalchemy.text("SELECT SUM(red_ml) FROM potions WHERE name = :potion"),[{"potion": low_potion}]).scalar()
            green_needed = conn.execute(sqlalchemy.text("SELECT SUM(green_ml) FROM potions WHERE name = :potion"),[{"potion": low_potion}]).scalar()
            blue_needed = conn.execute(sqlalchemy.text("SELECT SUM(blue_ml) FROM potions WHERE name = :potion"),[{"potion": low_potion}]).scalar()
            dark_needed = conn.execute(sqlalchemy.text("SELECT SUM(dark_ml) FROM potions WHERE name = :potion"),[{"potion": low_potion}]).scalar()
            wallet = conn.execute(sqlalchemy.text("SELECT gold FROM shop_inventory")).scalar()
    #traverse catalog
    for barrel in wholesale_catalog:
        while(red_needed > 0 or green_needed > 0 or blue_needed > 0 or dark_needed > 0):
            # if GREEN barrel in catalog
            if barrel.potion_type == [0,1, 0, 0] and green_needed > 0 and barrel.quantity and barrel.price < wallet: 
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
            # if RED barrel in catalog
            elif (barrel.potion_type == [1, 0, 0, 0]) and red_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
            # if BLUE barrel in catalog
            elif barrel.potion_type == [0, 0, 1, 0] and blue_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
                # if DARK barrel in catalog
            elif barrel.potion_type == [0, 0, 0, 1] and dark_needed > 0 and barrel.quantity and barrel.price < wallet:
                wallet -= barrel.price
                green_needed -= barrel.ml_per_barrel
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
    return purchase
