from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    green_ml_used = 0
    red_ml_used = 0
    blue_ml_used = 0
    dark_ml_used = 0
    with db.engine.begin() as conn:
        for potion in potions_delivered:
            sku = conn.execute(sqlalchemy.text("""
                        SELECT sku 
                        FROM potions
                        WHERE red_ml = :red AND green_ml = :green AND blue_ml = :blue AND dark_ml = :dark
                        """),[{"red": potion.potion_type[0], "green": potion.potion_type[1], "blue": potion.potion_type[2], "dark": potion.potion_type[3]}]).scalar()
            conn.execute(sqlalchemy.text("""
                        INSERT INTO potion_ledger (potion_sku, change)
                        VALUES(:potion_id, :quantity)
                        """),[{"potion_id": sku, "quantity": potion.quantity}])
            red_ml_used -= (potion.potion_type[0] * potion.quantity)
            green_ml_used -= (potion.potion_type[1] * potion.quantity)
            blue_ml_used -= (potion.potion_type[2] * potion.quantity)
            dark_ml_used -= (potion.potion_type[3] * potion.quantity)
        conn.execute(sqlalchemy.text("""
                        INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
                        VALUES(:redML, :greenML, :blueML, :darkML)
                        """),[{"redML": red_ml_used, "greenML": green_ml_used, "blueML": blue_ml_used, "darkML": dark_ml_used}])
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    plan = {}
    with db.engine.begin() as conn:
        capacity = 10000
        low_potion = conn.execute(sqlalchemy.text("SELECT name FROM potions ORDER BY inventory ASC LIMIT 1")).scalar_one()
        red_needed, green_needed, blue_needed, dark_needed = conn.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM potions WHERE name = :low_potion"), [{"low_potion": low_potion}]).scalar()
        green_stock, red_stock, blue_stock, dark_stock = conn.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM shop_inventory")).scalar()
        low_quantity = 0
        green_bottles = 0
        red_bottles = 0
        blue_bottles = 0
        dark_bottles = 0
        while(green_stock >= green_needed and red_stock >= red_needed and blue_stock >= blue_needed and dark_stock >= dark_needed):
            green_stock -= green_needed
            red_stock -= red_needed
            blue_stock -= blue_needed
            dark_stock -= dark_needed
            low_quantity += 1
        if low_quantity:
            plan.update({
                    "potion_type": [red_needed, green_needed, blue_needed, dark_needed],
                    "quantity": low_potion,
                })
        while green_stock >= 100:
            green_bottles += 1
            green_stock -= 100
        if green_bottles:
            plan.update({
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_bottles,
                })
        while red_stock >= 100:
            red_bottles += 1
            red_stock -= 100
        if red_bottles:
            plan.update({
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_bottles,
                })
        while blue_stock >= 100:
            blue_bottles += 1
            blue_stock -= 100
        if blue_bottles:
            plan.update({
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_bottles,
                })
        while dark_stock >= 100:
            dark_bottles += 1
            dark_stock -= 100
        if dark_bottles:
            plan.update({
                    "potion_type": [0, 0, 0, 100],
                    "quantity": dark_bottles,
                })
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
