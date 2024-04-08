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
    spent = 0
    ml_bought = 0
    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        ml_bought += (barrel.ml_per_barrel * barrel.quantity)
    with db.engine.begin() as connection:
        num_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        num_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        num_ml += ml_bought
        num_gold -= spent
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold num_gold, num_green_ml = num_ml"))
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    green_purchase = 0
    with db.engine.begin() as connection:
        num_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
    if num_potions < 10:
        green_purchase = 1
    return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": green_purchase,
        }
    ]
