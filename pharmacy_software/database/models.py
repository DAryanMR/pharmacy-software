import sqlite3

# Connect to the SQLite database
# conn = sqlite3.connect('pharmacy.db')
conn = sqlite3.connect('database/pharmacy.db')
cursor = conn.cursor()


# # Drop the Users table if it exists
# cursor.execute('''
#     DROP TABLE IF EXISTS Users
# ''')

# # Create the Users table
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS Users (
#         id INTEGER PRIMARY KEY,
#         username TEXT,
#         password TEXT,
#         role TEXT
#     )
# ''')

cursor.execute('''
    DROP TABLE IF EXISTS Monitors
''')

cursor.execute('''
               Create table IF NOT EXISTS  Monitors (
                   m_id INTEGER PRIMARY KEY,
                   date TEXT,
                   u_id INTEGER,
                   login_time TEXT,
                   logout_time TEXT
                   )
               ''')

cursor.execute('''
    DROP TABLE IF EXISTS Expenses
''')

# Create the Expenses table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Expenses (
        id INTEGER PRIMARY KEY,
        e_id INTEGER,
        date TEXT,
        type TEXT,
        amount REAL
    )
''')

# Drop the MedicineSales table if it exists
cursor.execute('''
    DROP TABLE IF EXISTS MedicineSales
''')


# Create the MedicineSales table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS MedicineSales (
        sale_id INTEGER PRIMARY KEY,
        memo_id INTEGER,
        user_id INTEGER,
        date TEXT,
        customer_name TEXT,
        category_id INTEGER,
        item_id INTEGER,
        quantity INTEGER,
        amount REAL,
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (category_id) REFERENCES Categories(id),
        FOREIGN KEY (item_id) REFERENCES Items(id)
        UNIQUE (memo_id, category_id, item_id)
    )
''')

# Drop the ItemLedgers table if it exists
cursor.execute('''
    DROP TABLE IF EXISTS ItemLedgers
''')

# Create the ItemLedgers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ItemLedgers (
        ledger_id INTEGER PRIMARY KEY,
        item_id INTEGER,
        date TEXT,
        opening INTEGER DEFAULT 0,
        purchase INTEGER DEFAULT 0,
        sale INTEGER DEFAULT 0,
        return_sale INTEGER DEFAULT 0,
        return_buy INTEGER DEFAULT 0,
        issue INTEGER DEFAULT 0,
        closing INTEGER DEFAULT 0,
        FOREIGN KEY (item_id) REFERENCES Items(id)
    )
''')

# # Define the items
# ledgers = [
#     # 6 300 5 0 0 0 305
#     # 6 305 15 5 0 0 315
#     # 7 315 0 15 0 0 300
#     # 8 300 0 0 0 0 300
#     (10, "06-01-2024", 5, 0, 0, 0),
#     (10, "06-01-2024", 0, 10, 0, 0),
#     (10, "06-01-2024", 5, 10, 0, 0),
#     (10, "07-01-2024", 0, 50, 0, 0),
#     (10, "07-01-2024", 15, 0, 0, 0),
#     (10, "07-01-2024", 0, 0, 5, 0),
#     (10, "08-01-2024", 5, 0, 0, 0),
#     (10, "08-01-2024", 0, 0, 0, 1),
# ]

# # Insert the items into the Items table
# cursor.executemany(
#     "INSERT INTO ItemLedgers (item_id, date, purchase,sale,return_sale, return_buy) VALUES (?,?,?,?,?,?)",
#     ledgers
# )

# # Commit the changes
# conn.commit()

cursor.execute('''
    DROP TABLE IF EXISTS MedicinePurchases
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS MedicinePurchases (
        purchase_id INTEGER PRIMARY KEY,
        invoice_id INTEGER,
        user_id INTEGER,
        date TEXT,
        supplier_id INTEGER,
        remarks TEXT,
        quantity INTEGER,
        category_id INTEGER,
        item_id INTEGER,
        amount REAL,
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
        FOREIGN KEY (category_id) REFERENCES Categories(id),
        FOREIGN KEY (item_id) REFERENCES Items(id),
        UNIQUE (invoice_id, category_id, item_id)
    )
''')

cursor.execute('''
    DROP TABLE IF EXISTS Suppliers
''')

# Create the Suppliers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Suppliers (
        supplier_id INTEGER PRIMARY KEY,
        supplier_name TEXT
    )
''')


cursor.execute('''
    DROP TABLE IF EXISTS MedicineInfos
''')

# Create the MedicineInfos table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS MedicineInfos (
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER,
        category_id INTEGER,
        item_id INTEGER,
        purchase_rate REAL,
        sell_rate REAL,
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
        FOREIGN KEY (category_id) REFERENCES Categories(id),
        FOREIGN KEY (item_id) REFERENCES Items(id)
    )
''')

# Drop the Items table if it exists
cursor.execute('''
    DROP TABLE IF EXISTS Categories
''')

# Create the Categories table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Categories (
        id INTEGER PRIMARY KEY,
        category_name TEXT
    )
''')

# Drop the Items table if it exists
cursor.execute('''
    DROP TABLE IF EXISTS Items
''')

# Create the Items table
cursor.execute('''
    CREATE TABLE Items (
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER,
        category_id INTEGER,
        item_name TEXT,
        item_count INTEGER,
        buy_rate REAL DEFAULT 0,
        sell_rate REAL DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES Categories(id),
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
    )
''')


# # Get the schema for the MedicineSales table
# cursor.execute("PRAGMA table_info(MedicineSales)")
# medicine_sales_schema = cursor.fetchall()

# # Get the schema for the MedicinePurchases table
# cursor.execute("PRAGMA table_info(MedicinePurchases)")
# medicine_purchases_schema = cursor.fetchall()

# # Get the schema for the Suppliers table
# cursor.execute("PRAGMA table_info(Suppliers)")
# suppliers_schema = cursor.fetchall()

# # Get the schema for the MedicineInfos table
# cursor.execute("PRAGMA table_info(MedicineInfos)")
# medicine_infos_schema = cursor.fetchall()

# # Get the schema for the Categories table
# cursor.execute("PRAGMA table_info(Categories)")
# categories_schema = cursor.fetchall()

# # Get the schema for the Items table
# cursor.execute("PRAGMA table_info(Items)")
# items_schema = cursor.fetchall()


# print("\nMedicineSales Table Schema:")
# for column in medicine_sales_schema:
#     print(column)

# print("\nMedicinePurchases Table Schema:")
# for column in medicine_purchases_schema:
#     print(column)

# print("\nSuppliers Table Schema:")
# for column in suppliers_schema:
#     print(column)

# print("\nMedicineInfos Table Schema:")
# for column in medicine_infos_schema:
#     print(column)

# print("\nCategories Table Schema:")
# for column in categories_schema:
#     print(column)

# print("\nItems Table Schema:")
# for column in items_schema:
#     print(column)

# # Define the user data
# user_data = ('demouser', 'abcde', 'employee')

# # Insert the user into the Users table
# cursor.execute("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)", user_data)

# # Commit the changes and close the connection
# conn.commit()

# # # Retrieve all rows from the Users table
# cursor.execute("SELECT * FROM  ItemLedgers")

# rows = cursor.fetchall()

# # # Print the rows
# for row in rows:
#     print(row)

# conn.close()
