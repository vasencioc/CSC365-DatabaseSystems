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
    with db.engine.begin() as conn:
        for customer in customers:
            Name = customer.customer_name
            Class = customer.character_class
            Level = customer.level
            customerID = conn.execute(sqlalchemy.text("SELECT customer_id FROM customers WHERE name = :Name AND level = :Level AND class = :Class"),
                         [{"Name": Name, "Level": Level, "Class":Class}]).scalar()
            if(customerID is None):
                customerID = conn.execute(sqlalchemy.text("INSERT INTO customers (name, level, class) VALUES (:Name, :Level, :Class) RETURNING customer_id"),
                         [{"Name": Name, "Level": Level, "Class":Class}]).scalar()
            conn.execute(sqlalchemy.text("INSERT INTO visits (visit_id, customer_id) VALUES (:visitID, :customerID)"), [{"visitID": visit_id, "customerID": customerID}])
    print(customers)
    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    Name = new_cart.customer_name
    Class = new_cart.character_class
    Level = new_cart.level
    with db.engine.begin() as conn:
        id = conn.execute(sqlalchemy.text("SELECT customer_id FROM customers WHERE name = :Name AND level = :Level AND class = :Class"),
                         [{"Name": Name, "Level": Level, "Class":Class}]).scalar()
        cartID = conn.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:id) RETURNING cart_id"), [{"id": id}]).scalar()
    return {"cart_id": cartID}

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as conn:
        customerID = conn.execute(sqlalchemy.text("SELECT customer_id FROM carts WHERE cart_id = :cartID"), [{"cartID": cart_id}]).scalar()
        conn.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, customer_id, potion, quantity) VALUES (:cartID, :customerID, :sku, :quantity)"),
                     [{"cartID": cart_id, "customerID": customerID, "sku": item_sku, "quantity": cart_item.quantity}])
    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    total_paid = 0
    total_bought = 0
    with db.engine.begin() as conn:
        items = conn.execute(sqlalchemy.text("SELECT potion, quantity FROM cart_items JOIN carts ON cart_items.cart_id = carts.cart_id WHERE carts.cart_id = :cartID"),
                             {"cartID": cart_id}).scalar()
        for potion, quantity in items:
            total_bought += quantity
            conn.execute(sqlalchemy.text("UPDATE potions SET inventory = inventory - :item_quantity WHERE sku = :item_potion"), [{"item_quantity": quantity, "item_potion": potion}])
            price = conn.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :item_potion"), {"item_potion": potion})
            spent = quantity * price
            total_paid += spent
            conn.execute(sqlalchemy.text("UPDATE shop_inventory SET gold = gold - :spent"), {"spent": spent})
        conn.execute(sqlalchemy.text("DELETE FROM cart_items WHERE cart_id = :cartID"), {"cartID":cart_id})
        conn.execute(sqlalchemy.text("DELETE FROM carts WHERE cart_id = :cartID"), {"cartID":cart_id})
    return {"total_potions_bought": total_bought, "total_gold_paid": total_paid}
