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
    green_ml_bought = 0
    red_ml_bought = 0
    blue_ml_bought = 0
    dark_ml_bought = 0
    spent = 0
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            spent += (barrel.price * barrel.quantity)
            red_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[0])
            green_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[1])
            blue_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[2])
            dark_ml_bought += (barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[3])
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold) VALUES (:gold)"), {"gold": (spent * -1)})
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml) 
                                              VALUES (:redML, :greenML, :blueML, :darkML)"""), 
                                          [{"redML": red_ml_bought, "greenML": green_ml_bought, "blueML": blue_ml_bought, "darkML": dark_ml_bought}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # med $250 -2500ml
    # sm $100 -500ml
    # mini $60 -200ml
    purchase = []
    capacity = 1000
    print(wholesale_catalog)
    with db.engine.begin() as conn:
        wallet = conn.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledger")).scalar()
        stock = conn.execute(sqlalchemy.text("""
                                            SELECT COALESCE(SUM(red_ml), 0) AS red, COALESCE(SUM(green_ml), 0) AS green,
                                                    COALESCE(SUM(blue_ml), 0) AS blue, COALESCE(SUM(dark_ml), 0) AS dark
                                            FROM ml_ledger""")).first()
        red, green, blue, dark = stock.red, stock.green, stock.blue, stock.dark
        level = red + green + blue + dark
    #traverse catalog
    for barrel in wholesale_catalog:
        #only buying mini barrels for now
        if(barrel.ml_per_barrel == 200 and (level + 200) < capacity and wallet > 60):
                wallet -= barrel.price
                level += 200
                purchase.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })

    return purchase
