import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('database/pharmacy.db')
cursor = conn.cursor()

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
# categories = [
#     ('TABLET',),
# ]

# Insert the categories into the Categories table
cursor.executemany(
    "INSERT INTO Categories (category_name) VALUES (?)", categories)

# Commit the changes
conn.commit()

# Retrieve all rows from the Categories table
cursor.execute("SELECT * FROM Categories")
rows = cursor.fetchall()

# Print the rows
for row in rows:
    print(row)

conn.close()
