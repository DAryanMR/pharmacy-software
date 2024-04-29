import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('database/pharmacy.db')
cursor = conn.cursor()


'''

# Define the suppliers data
categories = [
    ('BANDAGE',), # 1
    ('CANNULA',), # 2
    ('CAPSULE',), # 3
    ('CATGUT',), # 4
    ('CONDOM',), # 5
    ('DPS',), # 6
    ('DROPS',), # 7
    ('INHALER',), # 8
    ('INSULIN',), # 9
    ('INJECTION',), # 10
    ('LOTION',), # 11
    ('MOUTH WASH',), # 12
    ('OINTMENT,CREAM',), # 13
    ('ORS',), # 14
    ('OTHERS',), # 15
    ('PAMPUS, WET TISSUE & FEEDER ALL',), # 16
    ('POWDER & MILK ALL ITEM',), # 17
    ('PREGNANCY STRIP',), # 18
    ('PROLENE',), # 19
    ('SANITARY PAD',), # 20
    ('SET',), # 21
    ('SHAMPOO',), # 22
    ('SILK',), # 23
    ('SPRAY',), # 24
    ('SUPPOSITORIES',), # 25
    ('SURGICAL',), # 26
    ('SYRUP',), # 27
    ('TOOTH PASTE & BRUSH',), # 28
    ('TABLET',), # 29
    ('VICRYL',), # 30
]

'''




# Define the items
items = [
    (1, 17, 'NEBANOL', 0, 0, 0),
    (1, 17, 'NORMO K', 0, 0, 0),
    (2, 17, 'ACTERIA SACHET', 0, 0, 0),
    (3, 17, 'SERGEL 20MG POWDER', 0, 0, 0),
    (3, 17, 'FOSFOGEN', 0, 0, 0),
    (4, 17, 'GLUCOS D', 0, 0, 0),
    (5, 17, 'PREGARE POWDER', 0, 0, 0),
    (2, 17, 'UTIFOS 3MG SACHET', 0, 0, 0),
    (6, 17, 'ENO POWDER', 0, 0, 0),
]

# Insert the items into the Items table
cursor.executemany(
    "INSERT INTO Items (supplier_id, category_id, item_name, item_count,buy_rate,sell_rate) VALUES (?, ?, ?, ?,?,?)",
    items
)

# Commit the changes
conn.commit()

# Retrieve all rows from the Items table
cursor.execute("SELECT * FROM Items")
rows = cursor.fetchall()

# Print the rows
for row in rows:
    print(row)

conn.close()
