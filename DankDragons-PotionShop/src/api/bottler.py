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
    with db.engine.begin() as connection:
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
    while green_ml >= 100:
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
    # Each bottle has a quantity of what proportion of red, green, blue, and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
