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
            ml_bought = (barrel.ml_per_barrel * barrel.quantity)
            spent += (barrel.price * barrel.quantity) * (-1)
            if barrel.potion_type == [0, 1, 0, 0]:
                transaction = connection.execute(sqlalchemy.text("INSERT INTO shop_transactions (description) VALUES ('Green Barrels Delivered') RETURNING transaction_id")).scalar()
                connection.execute(sqlalchemy.text("""
                                           INSERT INTO shop_ledger_entries (item_id, transaction, change)
                                           VALUES(:barrel_item_id, :transaction, :ml_bought),(:gold_item_id, :transaction, :spent
                                           """),[{"barrel_item_id": 3, "transaction": transaction, "ml_bought": ml_bought, "gold_item_id": 1, "spent": spent}])
            elif barrel.potion_type == [1, 0, 0, 0]:
                transaction = connection.execute(sqlalchemy.text("INSERT INTO shop_transactions (description) VALUES ('Red Barrels Delivered') RETURNING transaction_id")).scalar()
                connection.execute(sqlalchemy.text("""
                                           INSERT INTO shop_ledger_entries (item_id, transaction, change)
                                           VALUES(:barrel_item_id, :transaction, :ml_bought),(:gold_item_id, :transaction, :spent
                                           """),[{"barrel_item_id": 2, "transaction": transaction, "ml_bought": ml_bought, "gold_item_id": 1, "spent": spent}])
            elif barrel.potion_type == [0, 0, 1, 0]:
                transaction = connection.execute(sqlalchemy.text("INSERT INTO shop_transactions (description) VALUES ('Blue Barrels Delivered') RETURNING transaction_id")).scalar()
                connection.execute(sqlalchemy.text("""
                                           INSERT INTO shop_ledger_entries (item_id, transaction, change)
                                           VALUES(:barrel_item_id, :transaction, :ml_bought),(:gold_item_id, :transaction, :spent
                                           """),[{"barrel_item_id": 4, "transaction": transaction, "ml_bought": ml_bought, "gold_item_id": 1, "spent": spent}])
            elif barrel.potion_type == [0, 0, 0, 1]:
                transaction = connection.execute(sqlalchemy.text("INSERT INTO shop_transactions (description) VALUES ('Dark Barrels Delivered') RETURNING transaction_id")).scalar()
                connection.execute(sqlalchemy.text("""
                                           INSERT INTO shop_ledger_entries (item_id, transaction, change)
                                           VALUES(:barrel_item_id, :transaction, :ml_bought),(:gold_item_id, :transaction, :spent
                                           """),[{"barrel_item_id": 5, "transaction": transaction, "ml_bought": ml_bought, "gold_item_id": 1, "spent": spent}])
            else:
                raise Exception("Invalid Barrel Type")
        gold_change = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_ledger_entries WHERE item_id = :gold_item_id"), [{"gold_item_id": 1}]).scalar()
        red_change = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_ledger_entries WHERE item_id = :barrel_item_id"), [{"barrel_item_id": 2}]).scalar()
        green_change = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_ledger_entries WHERE item_id = :barrel_item_id"), [{"barrel_item_id": 3}]).scalar()
        blue_change = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_ledger_entries WHERE item_id = :barrel_item_id"), [{"barrel_item_id": 4}]).scalar()
        dark_change = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_ledger_entries WHERE item_id = :barrel_item_id"), [{"barrel_item_id": 5}]).scalar()
        connection.execute(sqlalchemy.text("UPDATE shop_inventory SET amount = amount + :change WHERE item_id = :item"),[{"amount": gold_change,"item_id": 1}])
        connection.execute(sqlalchemy.text("UPDATE shop_inventory SET amount = amount + :change WHERE item_id = :item"),[{"amount": red_change,"item_id":2}])
        connection.execute(sqlalchemy.text("UPDATE shop_inventory SET amount = amount + :change WHERE item_id = :item"),[{"amount": green_change,"item_id": 3}])
        connection.execute(sqlalchemy.text("UPDATE shop_inventory SET amount = amount + :change WHERE item_id = :item"),[{"amount": blue_change,"item_id": 4}])
        connection.execute(sqlalchemy.text("UPDATE shop_inventory SET amount = amount + :change WHERE item_id = :item"),[{"amount": dark_change,"item_id": 5}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    capacity = 10000
    purchase = []
    print(wholesale_catalog)
    with db.engine.begin() as conn:
        low_potion = conn.execute(sqlalchemy.text("SELECT name FROM potions ORDER BY inventory ASC LIMIT 1")).scalar_one()
        potions_needed = conn.execute(sqlalchemy.text("SELECT SUM(inventory)FROM potions")).scalar() - 50
        redML = conn.execute(sqlalchemy.text("SELECT amount FROM global_inventory WHERE item_id = :id"), [{"id": 2}]).scalar()
        greenML = conn.execute(sqlalchemy.text("SELECT amount FROM global_inventory WHERE item_id = :id"), [{"id": 3}]).scalar()
        blueML = conn.execute(sqlalchemy.text("SELECT amount FROM global_inventory WHERE item_id = :id"), [{"id": 4}]).scalar()
        darkML = conn.execute(sqlalchemy.text("SELECT amount FROM global_inventory WHERE item_id = :id"), [{"id": 5}]).scalar()
        if(potions_needed != 0):
            red_needed, green_needed, blue_needed, dark_needed = conn.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM potions WHERE name = :potion"), [{"potion": low_potion}]).scalar()
            wallet = conn.execute(sqlalchemy.text("SELECT gold FROM shop_inventory")).scalar()
    curr_capacity = greenML+redML+blueML+darkML
    #traverse catalog
    for barrel in wholesale_catalog:
        while(curr_capacity <= capacity):
            if(red_needed > 0 or green_needed > 0 or blue_needed > 0 or dark_needed > 0):
                # if GREEN barrel in catalog
                if barrel.potion_type == [0,1, 0, 0] and green_needed > 0 and barrel.quantity and barrel.price < wallet: 
                    wallet -= barrel.price
                    green_needed -= barrel.ml_per_barrel
                    curr_capacity += barrel.ml_per_barrel
                    purchase.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                # if RED barrel in catalog
                elif (barrel.potion_type == [1, 0, 0, 0]) and red_needed > 0 and barrel.quantity and barrel.price < wallet:
                    wallet -= barrel.price
                    red_needed -= barrel.ml_per_barrel
                    curr_capacity += barrel.ml_per_barrel
                    purchase.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                # if BLUE barrel in catalog
                elif barrel.potion_type == [0, 0, 1, 0] and blue_needed > 0 and barrel.quantity and barrel.price < wallet:
                    wallet -= barrel.price
                    blue_needed -= barrel.ml_per_barrel
                    curr_capacity += barrel.ml_per_barrel
                    purchase.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # if DARK barrel in catalog
                elif barrel.potion_type == [0, 0, 0, 1] and dark_needed > 0 and barrel.quantity and barrel.price < wallet:
                    wallet -= barrel.price
                    dark_needed -= barrel.ml_per_barrel
                    curr_capacity += barrel.ml_per_barrel
                    purchase.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
    return purchase
