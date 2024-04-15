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
    new_green = 0
    green_ml_used = 0
    new_red = 0
    red_ml_used = 0
    new_blue = 0
    blue_ml_used = 0
    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:
            new_green += potion.quantity
            green_ml_used += (potion.quantity * 100)
        elif potion.potion_type == [100, 0, 0, 0]:
            new_red += potion.quantity
            red_ml_used += (potion.quantity * 100)
        elif potion.potion_type == [0, 0, 100, 0]:
            new_blue += potion.quantity
            blue_ml_used += (potion.quantity * 100)
    with db.engine.begin() as connection:
        # update green
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        green_bottles = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        green_bottles += new_green
        green_ml -= green_ml_used
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {green_bottles}, num_green_ml = {green_ml}"))
        # update red
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        red_bottles = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        red_bottles += new_red
        red_ml -= red_ml_used
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {red_bottles}, num_red_ml = {red_ml}"))
        # update blue
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        blue_bottles = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        blue_bottles += new_blue
        blue_ml -= blue_ml_used
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {blue_bottles}, num_blue_ml = {blue_ml}"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    plan = []
    green_bottles = 0
    red_bottles = 0
    blue_bottles = 0
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
