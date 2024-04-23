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
            conn.execute(sqlalchemy.text(
                "UPDATE potions SET quantity = quantity + new_pots WHERE red_ml = :red AND green_ml = :green AND blue_ml = :blue AND dark_ml = :dark"),
                         [{"new_pots": potion.quantity, "red": potion.potion_type[0], "green": potion.potion_type[1], "blue": potion.potion_type[2], "dark": potion.potion_type[3]}])
            red_ml_used += potion.potion_type[0]
            green_ml_used += potion.potion_type[1]
            blue_ml_used += potion.potion_type[2]
            dark_ml_used += potion.potion_type[3]
        conn.execute(sqlalchemy.text(
                "UPDATE shop_inventory SET num_red_ml = num_red_ml - :red_used AND num_green_ml = num_green_ml - :green_used AND num_blue_ml = num_blue_ml - :blue_used AND num_dark_ml = num_dark_ml -:dark_used"),
                [{"red_used": red_ml_used, "green_used": green_ml_used, "blue_used": blue_ml_used, "dark_used":dark_ml_used}])
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    plan = {}
    with db.engine.begin() as conn:
        low_potion = conn.execute(sqlalchemy.text("SELECT name FROM potions ORDER BY quantity ASC LIMIT 1"))
        green_needed = conn.execute(sqlalchemy.text("SELECT green_ml FROM potions WHERE name = :low_potion"), [{"low_potion": low_potion}]).scalar()
        red_needed = conn.execute(sqlalchemy.text("SELECT red_ml FROM potions WHERE name = :low_potion"), [{"low_potion": low_potion}]).scalar()
        blue_needed = conn.execute(sqlalchemy.text("SELECT blue_ml FROM potions WHERE name = :low_potion"), [{"low_potion": low_potion}]).scalar()
        dark_needed = conn.execute(sqlalchemy.text("SELECT dark_ml FROM potions WHERE name = :low_potion"), [{"low_potion": low_potion}]).scalar()
        green_stock = conn.execute(sqlalchemy.text("SELECT num_green_ml FROM shop_inventory"))
        red_stock = conn.execute(sqlalchemy.text("SELECT num_red_ml FROM shop_inventory"))
        blue_stock = conn.execute(sqlalchemy.text("SELECT num_blue_ml FROM shop_inventory"))
        dark_stock = conn.execute(sqlalchemy.text("SELECT num_dark_ml FROM shop_inventory"))
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
            plan.append({
                    "potion_type": [red_needed, green_needed, blue_needed, dark_needed],
                    "quantity": low_potion,
                })
        while green_stock >= 100:
            green_bottles += 1
            green_ml -= 100
        if green_bottles:
            plan.append({
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_bottles,
                })
        while red_ml >= 100:
            red_bottles += 1
            red_ml -= 100
        if red_bottles:
            plan.append({
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_bottles,
                })
        while blue_ml >= 100:
            blue_bottles += 1
            blue_ml -= 100
        if blue_bottles:
            plan.append({
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_bottles,
                })
        while dark_ml >= 100:
            dark_bottles += 1
            dark_ml -= 100
        if dark_bottles:
            plan.append({
                    "potion_type": [0, 0, 0, 100],
                    "quantity": dark_bottles,
                })
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
