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
        capacity = 50
        level = conn.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar()
        least_potion = conn.execute(sqlalchemy.text("SELECT potion_sku FROM potion_ledger ORDER BY SUM(change) ASC LIMIT 1")).scalar_one()
        red_needed, green_needed, blue_needed, dark_needed = conn.execute(sqlalchemy.text("""
                                                                        SELECT red_ml, green_ml, blue_ml, dark_ml 
                                                                        FROM potions
                                                                        WHERE sku = :least_potion"""), [{"least_potion": least_potion}]).scalar()
        red_stock, green_stock, blue_stock, dark_stock = conn.execute(sqlalchemy.text("""
                                                                        SELECT SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml)
                                                                        FROM ml_ledger""")).scalar()
        least_quantity = 0
        green_bottles = 0
        red_bottles = 0
        blue_bottles = 0
        dark_bottles = 0
        while(green_stock >= green_needed and red_stock >= red_needed and blue_stock >= blue_needed and dark_stock >= dark_needed and level < capacity):
            green_stock -= green_needed
            red_stock -= red_needed
            blue_stock -= blue_needed
            dark_stock -= dark_needed
            least_quantity += 1
            level += 1
        if least_quantity:
            plan.update({
                    "potion_type": [red_needed, green_needed, blue_needed, dark_needed],
                    "quantity": least_quantity,
                })
        while(level < (0.75 * capacity)):
            rand_potion = conn.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY RANDOM() LIMIT 1"))
            if(rand_potion.red_ml <= red_stock and rand_potion.green_ml <= red_stock and rand_potion.blue_ml <= blue_stock and rand_potion.dark_ml <= dark_stock):
                green_stock -= rand_potion.green_ml
                red_stock -= rand_potion.red_ml
                blue_stock -= rand_potion.blue_ml
                dark_stock -= rand_potion.dark_ml
                level += 1
                plan.update({
                    "potion_type": [rand_potion.red_ml, rand_potion.green_ml, rand_potion.blue_ml, rand_potion.dark_ml],
                    "quantity": 1,
                    })
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
