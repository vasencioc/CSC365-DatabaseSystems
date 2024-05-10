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
    with db.engine.begin() as conn:
        change_red = 0
        change_green = 0
        change_blue = 0
        change_dark = 0
        for potion in potions_delivered:
            sku = conn.execute(sqlalchemy.text("""
                        SELECT sku 
                        FROM potions
                        WHERE red_ml = :red AND green_ml = :green AND blue_ml = :blue AND dark_ml = :dark
                        """),[{"red": potion.potion_type[0], "green": potion.potion_type[1], "blue": potion.potion_type[2], "dark": potion.potion_type[3]}]).scalar()
            conn.execute(sqlalchemy.text("""
                        INSERT INTO potion_ledger (potion_sku, change)
                        VALUES(:potion_id, :quantity)
                        """),[{"potion_id": sku, "quantity": potion.quantity}])
            change_red += (potion.potion_type[0] * potion.quantity)
            change_green += (potion.potion_type[1] * potion.quantity)
            change_blue += (potion.potion_type[2] * potion.quantity)
            change_dark += (potion.potion_type[3] * potion.quantity)
        conn.execute(sqlalchemy.text("""
                        INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
                        VALUES(:redML, :greenML, :blueML, :darkML)
                        """),[{"redML": (change_red * -1), "greenML": (change_green * -1), "blueML": (change_blue * -1), "darkML": (change_dark * -1)}])
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    plan = []
    with db.engine.begin() as conn:
        capacity = 50
        least_quantity = 0
        stock = conn.execute(sqlalchemy.text("""
                                            SELECT COALESCE(SUM(red_ml), 0) red, COALESCE(SUM(green_ml), 0) green,
                                                    COALESCE(SUM(blue_ml), 0) blue, COALESCE(SUM(dark_ml), 0) dark
                                            FROM ml_ledger""")).first()
        red, green, blue, dark = stock.red, stock.green, stock.blue, stock.dark
        level = conn.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).scalar()
        least_potion = conn.execute(sqlalchemy.text("""
                                        SELECT potion_sku 
                                        FROM potion_ledger 
                                        GROUP BY potion_sku 
                                        ORDER BY SUM(change) ASC LIMIT 1""")).scalar()
        if least_potion is not None:
            needed  = conn.execute(sqlalchemy.text("""
                                            SELECT red_ml, green_ml, blue_ml, dark_ml 
                                            FROM potions
                                            WHERE sku = :least_potion"""), {"least_potion": least_potion}).first()
            needed_green, needed_red, needed_blue, needed_dark = needed.green_ml, needed.red_ml, needed.blue_ml, needed.dark_ml
            while(green  > needed_green and red > needed_red and blue > needed_blue and dark > needed_dark and level < capacity):
                green -= needed_green
                red -= needed_red
                blue -= needed_blue
                dark -= needed_dark
                least_quantity += 1
                level += 1
            if least_quantity:
                plan.append({
                        "potion_type": [needed_red, needed_green, needed_blue, needed_dark],
                        "quantity": least_quantity,
                    })
        stock_list = {"redStock":[red, [100, 0, 0, 0]], "greenStock": [green, [0, 100, 0, 0]],
                      "blueStock": [blue, [0, 0, 100, 0]], "darkStock": [dark, [0, 0, 0, 100]]}
        for _, stock_info in stock_list.items():
            quantity = 0
            while stock_info[0] > 0 and level < capacity:
                stock_info[0] -= 100
                level += 1
                quantity += 1
            if quantity:
                plan.append({
                    "potion_type": stock_info[1],
                    "quantity": quantity,
                })

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
