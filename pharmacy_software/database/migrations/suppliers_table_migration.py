import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('database/pharmacy.db')
cursor = conn.cursor()

# Define the suppliers data
supplier_data = [
    ('SQUARE',), #1
    ('RADIANT',), # 2
    ('HEALTHCARE PHARMA',), # 3
    ('UNI LIVER',), # 4
    ('RANATA',), # 5
    ('SMC',), # 6
    ('IBNA SINA',), # 7
    ('ACME',), # 8 
    ('ARISTO PHARMA',), # 9
    ('INCEPTA',), # 10
    ('OPSONIN',), # 11
    ('NOVARTIS ',), # 12
    ('BEXIMCO',), # 13
    ('JAYSON PHARMA',), # 14
    ('BIOPHARMA',), # 15
    ('FOREIGN',), # 16
    ('FORIGHN',), # 17
    ('CTG SCIENTIST',), # 18
    ('PACIFIC',), # 19
    ('SOFT',), # 20
    ('TIBBET',), # 21
    ('BASHUNDHARA',), # 22
    ('HOKKANI',), # 23
    ('FRESH',), # 24
    ('RENATA LTD',), # 25
    ('ACI',), # 26
    ('S.A TALIORS',), # 27
    ('LATEX',), # 28
    ('CHINA',), # 29
    ('DISOVAN',), # 30
    ('GALAXY MEDICARE',), # 31
    ('MOMTAZ',), # 32
    ('CIGMA',), # 33
    ('DISOVAN',), # 34
    ('ETHICON',), # 35
    ('EGYPT',), # 36
    ('POPULAR',), # 37
    ('LIBRA',), # 38
    ('LIBAR',), # 39
    ('GANO SHASTA',), # 40
    ('GANO SHAATA',), # 41
    ('DRUG INTERNAT',), # 42
    ('GSK',), # 43
    ('SQUARE TOILETRI',), # 44
    ('THAI CORPORATION LTD',), # 45
    ('UNIMED UNIHEALTH',), # 46
    ('ACI LID',), # 47
    ('SUN PHARMA',), # 48
    ('GENERAL PHARMA',), # 49
]

# Insert the suppliers into the Suppliers table
cursor.executemany(
    "INSERT INTO Suppliers (supplier_name) VALUES (?)", supplier_data)

# Commit the changes
conn.commit()

# Retrieve all rows from the Suppliers table
cursor.execute("SELECT * FROM Suppliers")
rows = cursor.fetchall()

# Print the rows
for row in rows:
    print(row)

conn.close()
