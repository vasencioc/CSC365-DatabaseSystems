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
    with db.engine.begin() as conn:
        num_potions = conn.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar()
        num_ml = conn.execute(sqlalchemy.text("SELECT SUM(red_ml + green_ml + blue_ml + dark_ml) FROM ml_ledger")).scalar()
        num_gold = conn.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledger")).scalar()
    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": num_gold}

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
    Start with 1 capacity for 50 potions and 1
    capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    return "OK"
