from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as conn:
        conn.execute(sqlalchemy.text("TRUNCATE potion_ledger"))
        conn.execute(sqlalchemy.text("TRUNCATE ml_ledger"))
        conn.execute(sqlalchemy.text("TRUNCATE visits"))
        conn.execute(sqlalchemy.text("TRUNCATE customers CASCADE"))
        conn.execute(sqlalchemy.text("TRUNCATE gold_ledger"))
        conn.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold) VALUES (:starting_bank)"), {"starting_bank": 100})
    return "OK"
