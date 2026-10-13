CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 1792a942441c

CREATE TABLE categories (
    id INTEGER NOT NULL AUTO_INCREMENT, 
    name VARCHAR(120) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE users (
    id INTEGER NOT NULL AUTO_INCREMENT, 
    name VARCHAR(120) NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    `role` VARCHAR(20) NOT NULL, 
    active BOOL NOT NULL, 
    failed_logins INTEGER NOT NULL, 
    locked_until DATETIME, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_user_role CHECK (role IN ('manager', 'researcher')), 
    UNIQUE (email)
);

CREATE TABLE auth_sessions (
    token_hash VARCHAR(64) NOT NULL, 
    user_id INTEGER NOT NULL, 
    expires_at DATETIME NOT NULL, 
    PRIMARY KEY (token_hash), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE products (
    id INTEGER NOT NULL AUTO_INCREMENT, 
    sku VARCHAR(64) NOT NULL, 
    name VARCHAR(160) NOT NULL, 
    category_id INTEGER NOT NULL, 
    unit VARCHAR(30) NOT NULL, 
    lead_time_days INTEGER NOT NULL, 
    safety_stock NUMERIC(14, 3) NOT NULL, 
    overstock_multiplier NUMERIC(8, 3) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_product_lead_time CHECK (lead_time_days > 0), 
    CONSTRAINT ck_product_overstock CHECK (overstock_multiplier > 1), 
    CONSTRAINT ck_product_safety CHECK (safety_stock >= 0), 
    FOREIGN KEY(category_id) REFERENCES categories (id), 
    UNIQUE (sku)
);

CREATE TABLE inventory (
    product_id INTEGER NOT NULL, 
    on_hand NUMERIC(14, 3) NOT NULL, 
    confirmed_in_transit NUMERIC(14, 3) NOT NULL, 
    allocated NUMERIC(14, 3) NOT NULL, 
    updated_at DATETIME NOT NULL, 
    PRIMARY KEY (product_id), 
    CONSTRAINT ck_inventory_allocated CHECK (allocated >= 0 AND allocated <= on_hand), 
    CONSTRAINT ck_inventory_transit CHECK (confirmed_in_transit >= 0), 
    CONSTRAINT ck_inventory_on_hand CHECK (on_hand >= 0), 
    FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE TABLE sales (
    id INTEGER NOT NULL AUTO_INCREMENT, 
    product_id INTEGER NOT NULL, 
    sale_date DATETIME NOT NULL, 
    quantity NUMERIC(14, 3) NOT NULL, 
    unit_price NUMERIC(14, 2) NOT NULL, 
    source VARCHAR(20) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_sale_source CHECK (source IN ('operational', 'historical')), 
    CONSTRAINT ck_sale_quantity CHECK (quantity > 0), 
    CONSTRAINT ck_sale_price CHECK (unit_price >= 0), 
    FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE INDEX ix_sales_product_id ON sales (product_id);

CREATE INDEX ix_sales_sale_date ON sales (sale_date);

INSERT INTO alembic_version (version_num) VALUES ('1792a942441c');

