CREATE table
  customers (
    customer_id int generated always as identity not null PRIMARY KEY,
    created_at timestamp with time zone null default now(),
    name text not null,
    level int not null,
    class text not null
  );

CREATE table
  carts (
    cart_id int generated always as identity not null PRIMARY KEY,
    created_at timestamp with time zone null default now(),
    customer_id int REFERENCES customers (customer_id)
  );

  CREATE table
  cart_items (
    cart_id int REFERENCES  carts (cart_id),
    customer_id int REFERENCES Customers (customer_id),
    potion text not null,
    quantity int not null
  );