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
    all_results = []
    results = []
    results_prev = []
    results_next = []
    with db.engine.begin() as conn:
        if customer_name and potion_sku:
            table_results = conn.execute(sqlalchemy.text("""SELECT cart_items.line_item_id, customers.timestamp, cart_items.quantity
                                                            FROM cart_items
                                                            JOIN carts ON cart_items.cart_id = carts.cart_id 
                                                            JOIN potions ON potions.sku = cart_items.potion
                                                            JOIN customers ON customers.customer_id = cart_items.customer_id
                                                            WHERE cart_items.potion = :SKU AND customers.name = :NAME
                                                            ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                            [{"SKU": potion_sku, "NAME": customer_name}])
            if table_results:
                for line_id, created_at, quantity in table_results:
                    line_total = conn.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :potion"), {"potion": potion_sku}).scalar()
                    line_total *= quantity
                    all_results.append({
                "line_item_id": line_id,
                "item_sku": potion_sku,
                "customer_name": customer_name,
                "line_item_total": line_total,
                "timestamp": created_at,
            })
        elif customer_name:
            table_results = conn.execute(sqlalchemy.text("""SELECT cart_items.line_item_id, customers.timestamp, cart_items.potion, cart_items.quantity
                                                            FROM cart_items
                                                            JOIN carts ON cart_items.cart_id = carts.cart_id 
                                                            JOIN potions ON potions.sku = cart_items.potion
                                                            JOIN customers ON customers.customer_id = cart_items.customer_id
                                                            WHERE customers.name = :NAME
                                                            ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                            [{"sort_col": sort_col, "sort_order": sort_order, "NAME": customer_name}])
            if table_results:
                for line_id, created_at, sku, quantity in table_results:
                    line_total = conn.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :potion"), {"potion": sku}).scalar()
                    line_total *= quantity
                    all_results.append({
                "line_item_id": line_id,
                "item_sku": sku,
                "customer_name": customer_name,
                "line_item_total": line_total,
                "timestamp": created_at,
            })
        elif potion_sku:
            table_results = conn.execute(sqlalchemy.text("""SELECT cart_items.line_item_id, customers.timestamp, customers.name, cart_items.quantity
                                                            FROM cart_items
                                                            JOIN carts ON cart_items.cart_id = carts.cart_id 
                                                            JOIN potions ON potions.sku = cart_items.potion
                                                            JOIN customers ON customers.customer_id = cart_items.customer_id
                                                            WHERE cart_items.potion = :SKU
                                                            ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                            [{"sort_col": sort_col, "sort_order": sort_order, "SKU": potion_sku}])
            if table_results:
                for line_id, created_at, Name, quantity in table_results:
                    line_total = conn.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :potion"), {"potion": potion_sku}).scalar()
                    line_total *= quantity
                    all_results.append({
                "line_item_id": line_id,
                "item_sku": potion_sku,
                "customer_name": Name,
                "line_item_total": line_total,
                "timestamp": created_at,
            })
        else:
            table_results = conn.execute(sqlalchemy.text("""SELECT line_item_id, customers.timestamp, customers.name, cart_items.potion, cart_items.quantity
                                                            FROM cart_items
                                                            JOIN carts ON cart_items.cart_id = carts.cart_id 
                                                            JOIN potions ON potions.sku = cart_items.potion
                                                            JOIN customers ON customers.customer_id = cart_items.customer_id
                                                            ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                            [{"sort_col": sort_col, "sort_order": sort_order}])
            if table_results:
                for line_id, created_at, Name, sku, quantity in table_results:
                    line_total = conn.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :potion"), {"potion": sku}).scalar()
                    line_total *= quantity
                    all_results.append({
                "line_item_id": line_id,
                "item_sku": sku,
                "customer_name": Name,
                "line_item_total": line_total,
                "timestamp": created_at,
            })
        if search_page == "":
            search_page = 0
        else: 
            search_page = int(search_page)
        if search_page > 1:
            results_prev = all_results[(((search_page - 1) * 5) - 5):(((search_page - 1) * 5) - 1)]
        results = all_results[((search_page * 5) - 5):((search_page * 5) - 1)]
        results_next = all_results[(((search_page + 1) * 5) - 5):(((search_page + 1) * 5) - 1)]
    return {
        "previous": results_prev,
        "next": results_next,
        "results": results
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
            conn.execute(sqlalchemy.text("""
                        INSERT INTO visits (visit_id, name, class, level) 
                        VALUES (:visitID, :Name, :Class, :Level)"""),
                        [{"visitID": visit_id, "Name": customer.customer_name, "Class": customer.character_class, "Level": customer.level}])
    print(customers)
    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as conn:
        id = conn.execute(sqlalchemy.text("INSERT INTO customers (name, level, class) VALUES (:Name, :Level, :Class) RETURNING customer_id"),
                         [{"Name": new_cart.customer_name, "Level": new_cart.level, "Class":new_cart.character_class}]).scalar()
        cartID = conn.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:id) RETURNING cart_id"), {"id": id}).scalar()
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
    with db.engine.begin() as conn:
        total_paid = 0
        total_bought = 0
        items = conn.execute(sqlalchemy.text("""SELECT potion, quantity, price
                                                FROM cart_items 
                                                JOIN carts ON cart_items.cart_id = carts.cart_id 
                                                JOIN potions ON potions.sku = cart_items.potion
                                                WHERE carts.cart_id = :cartID"""),
                                            {"cartID": cart_id})
        for item in items:
            potion, quantity, price = item.potion, item.quantity, item.price
            total_bought += quantity
            total_paid += (quantity * price)
            conn.execute(sqlalchemy.text("""INSERT INTO potion_ledger (potion_sku, change)
                                            VALUES(:potion_id, :quantity)"""),
                                        [{"potion_id": potion, "quantity": (quantity * -1)}])
        conn.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold) VALUES (:total_paid)"),
                                    {"total_paid": total_paid})
    return {"total_potions_bought": total_bought, "total_gold_paid": total_paid}
