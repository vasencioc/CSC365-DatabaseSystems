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
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {num_gold}, num_green_ml = {num_ml}"))
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    purchase = []
    print(wholesale_catalog)
    green_purchase = 0
    # red_purchase = 0
    # blue_purchase = 0
    with db.engine.begin() as connection:
        num_green = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        # num_red = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        # num_blue = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        wallet = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
    #traverse catalog
    for barrel in wholesale_catalog:
        # if GREEN barrel in catalog
        if barrel.potion_type == [0,100, 0, 0]:
            available_green = barrel.quantity
            if num_green < 10 and available_green: 
                wallet -= barrel.price
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        # # if RED barrel in catalog
        # if barrel.potion_type == [100, 0, 0, 0]:
        #     available_red = barrel.quantity
        #     if num_red < 10 and available_red:
        #             wallet -= barrel.price
        #             purchase.append({
        #                 "sku": barrel.sku,
        #                 "quantity": 1,
        #             })
        # # if BLUE barrel in catalog
        # if barrel.potion_type == [0, 0, 100, 0]:
        #     available_blue = barrel.quantity
        #     if num_red < 10 and available_blue:
        #             wallet -= barrel.price
        #             purchase.append({
        #                 "sku": barrel.sku,
        #                 "quantity": 1,
        #             })
    return purchase
