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
    green_ml_bought = 0
    red_ml_bought = 0
    blue_ml_bought = 0
    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        if barrel.potion_type == [0, 1, 0, 0]:
            green_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [1, 0, 0, 0]:
            red_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0, 0, 1, 0]:
            blue_ml_bought += (barrel.ml_per_barrel * barrel.quantity)
    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        num_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        num_green_ml += green_ml_bought
        num_red_ml += red_ml_bought
        num_blue_ml += blue_ml_bought
        num_gold -= spent
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {num_gold}, num_green_ml = {num_green_ml}, num_red_ml = {num_red_ml}, num_blue_ml = {num_blue_ml}"))
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    purchase = []
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        num_green = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        num_red = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        num_blue = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        wallet = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
    #traverse catalog
    for barrel in wholesale_catalog:
        # if GREEN barrel in catalog
        if barrel.potion_type == [0,1, 0, 0] and num_green < 10 and barrel.quantity and barrel.price < wallet: 
            wallet -= barrel.price
            purchase.append({
                "sku": barrel.sku,
                "quantity": 1,
            })
        # # if RED barrel in catalog
        elif (barrel.potion_type == [1, 0, 0, 0]) and num_red < 10 and barrel.quantity and barrel.price < wallet:
            wallet -= barrel.price
            purchase.append({
                "sku": barrel.sku,
                "quantity": 1,
            })
        # # if BLUE barrel in catalog
        elif barrel.potion_type == [0, 0, 1, 0] and num_blue < 10 and barrel.quantity and barrel.price < wallet:
            wallet -= barrel.price
            purchase.append({
                "sku": barrel.sku,
                "quantity": 1,
            })
    return purchase
