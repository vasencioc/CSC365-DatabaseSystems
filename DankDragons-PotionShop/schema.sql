CREATE table
  public.shop_inventory (
    num_green_ml integer not null default 0,
    gold integer not null default 100,
    num_red_ml integer not null default 0,
    num_blue_ml integer not null default 0,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (gold)
  ) tablespace pg_default;

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

CREATE table
  potions (
    sku int as identity not null PRIMARY KEY,
    created_at timestamp with time zone null default now(),
    name text not null,
    red_ml int not null,
    green_ml int not null,
    blue_ml int not null,
    dark_ml int not null,
    inventory int not null,
    price int not null
  );

CREATE table
  visits (
    visit_id int not null PRIMARY KEY,
    customer_id int REFERENCES customers (customer_id),
    created_at timestamp with time zone null default now()
  );
