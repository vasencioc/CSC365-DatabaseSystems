from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        cartID = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM Carts")).scalar()
        cartID += 1
        customerID = connection.execute(sqlalchemy.text("SELECT customer_ID FROM Customers WHERE name = new_cart.customer_name"))
        if customerID:
            connection.execute(sqlalchemy.text("INSERT INTO Carts (cart_ID, cutomer_ID) VALUES (cartID, customerID)"))
        else:
            customerID = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM Customers")).scalar()
            customerID += 1
            connection.execute(sqlalchemy.text("INSERT INTO Customers (cutomer_ID, name, class, level) VALUES (customerID, new_cart.customer_name, new_cart.character_class, new_cart.level)"))
            connection.execute(sqlalchemy.text("INSERT INTO Carts (cart_ID, cutomer_ID) VALUES (cartID, customerID)"))
    return {"cart_id": cartID}

class CartItem(BaseModel):
    quantity: int

################################################
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        customerID = connection.execute(sqlalchemy.text("SELECT customer_ID FROM Carts WHERE cart_ID = cart_id"))
        connection.execute(sqlalchemy.text("INSERT INTO Cart_Items (cart_ID, cutomer_ID, item_sku, quantity) VALUES (cart_id, customerID, item_sku, cart_item.quantity)")) 
    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    total_paid = 0
    with db.engine.begin() as connection:
        bank = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        green_inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        red_inventory = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        blue_inventory = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        green_bought = connection.execute(sqlalchemy.text("SELECT quantity FROM Cart_Items WHERE cart_ID = cart_id AND item_sku = 'GREEN_POTION_0'")).scalar()
        red_bought = connection.execute(sqlalchemy.text("SELECT quantity FROM Cart_Items WHERE cart_ID = cart_id AND item_sku = 'RED_POTION_0'")).scalar()
        blue_bought = connection.execute(sqlalchemy.text("SELECT quantity FROM Cart_Items WHERE cart_ID = cart_id AND item_sku = 'BLUE_POTION_0'")).scalar()
        total_bought = green_bought + red_bought + blue_bought
        if green_bought:
            green_inventory -= green_bought
            total_paid += (green_bought * 50)
        if red_bought:
            red_inventory -= red_bought
            total_paid += (red_bought * 50)
        if blue_bought:
            blue_inventory -= blue_bought
            total_paid += (blue_bought * 50)
        bank -= total_paid
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = green_inventory, num_red_potions = red_inventory, num_blue_potions = blue_inventory, gold = bank"))
        connection.execute(sqlalchemy.text("DELETE FROM Carts WHERE cart_ID = cart_id"))
        connection.execute(sqlalchemy.text("DELETE FROM Cart_Items WHERE cart_ID = cart_id"))
    return {"total_potions_bought": total_bought, "total_gold_paid": total_paid}
