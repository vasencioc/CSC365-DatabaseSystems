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
        stock = conn.execute(sqlalchemy.text("""
                                        SELECT SUM(red_ml) red, SUM(green_ml) green, SUM(blue_ml) blue, SUM(dark_ml) dark
                                        FROM ml_ledger""")).first()
        stock_red, stock_green, stock_blue, stock_dark = stock.red, stock.green, stock.blue, stock.dark
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
            stock_red -= (potion.potion_type[0] * potion.quantity)
            stock_green -= (potion.potion_type[1] * potion.quantity)
            stock_blue -= (potion.potion_type[2] * potion.quantity)
            stock_dark -= (potion.potion_type[3] * potion.quantity)
        conn.execute(sqlalchemy.text("""
                        INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
                        VALUES(:redML, :greenML, :blueML, :darkML)
                        """),[{"redML": stock_red, "greenML": stock_green, "blueML": stock_blue, "darkML": stock_dark}])
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    plan = []
    with db.engine.begin() as conn:
        capacity = 50
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
            needed_green, needed_red, needed_blue, needed_dark = needed.green_ml, needed.red_ml, needed.blue_ml, needed.dark
            least_quantity = 0
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
        rand_potion = conn.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY RANDOM() LIMIT 1")).first()
        rand_green, rand_red, rand_blue, rand_dark = rand_potion.green_ml, rand_potion.red_ml, rand_potion.blue_ml, rand_potion.dark_ml
        while(rand_red < red and rand_green < green and rand_blue < blue and rand_dark < dark and level < capacity):
            green -= rand_green
            red -= rand_red
            blue -= rand_blue
            dark -= rand_dark
            level += 1
            plan.append({
                "potion_type": [rand_red, rand_green, rand_blue, rand_dark],
                "quantity": 1,
                })
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
