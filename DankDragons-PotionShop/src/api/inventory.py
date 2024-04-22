from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from typing import Dict
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    catalog = {}
    with db.engine.begin() as conn:
        inventory = conn.execute(sqlalchemy.text("SELECT * FROM potions"))
        for name, quantity in inventory:
                catalog.append()
    return {"number_of_green_potions": num_green_potions, "green_ml_in_barrels": num_green_ml,
            "number_of_red_potions": num_red_potions, "red_ml_in_barrels": num_red_ml,
            "number_of_blue_potions": num_blue_potions, "blue_ml_in_barrels": num_blue_ml,
            "gold": num_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
