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
    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:
            new_green = new_green + potion.quantity
            ml_used = ml_used + (potion.quantity * 100)
    with db.engine.begin() as connection:
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        green_bottles = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        green_bottles += new_green
        green_ml -= ml_used
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = green_bottles"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = green_ml"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    green_bottles = 0
    with db.engine.begin() as connection:
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        while green_ml > 100:
            green_bottles += 1
            green_ml -= 100
         
    # Each bottle has a quantity of what proportion of red, green, blue, and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": green_bottles,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())
