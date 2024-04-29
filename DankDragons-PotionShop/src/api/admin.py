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
        conn.execute(sqlalchemy.text(
            "UPDATE global_inventory SET amount = 0"))
        conn.execute(sqlalchemy.text("UPDATE potions SET inventory = 0"))
        conn.execute(sqlalchemy.text("TRUNCATE customers CASCADE"))
    return "OK"
