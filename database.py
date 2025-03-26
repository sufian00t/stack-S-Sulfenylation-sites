import pandas as pd
import sqlite3

database_name = 'prediction_db.db'

df = pd. read_csv('C:\\Users\\Abu Sufian Rupok\\Desktop\\stack-S-Sulfenylation sites.csv')

conn = sqlite3.connect(database_name)

table_name = 'seq_prediction'
df.to_sql(table_name, conn, if_exists='replace', index=False)


conn = sqlite3.connect(database_name)
cursor = conn.cursor()

cursor.execute(f"SELECT * FROM {table_name}")
rows = cursor.fetchall()

print(f"Data in table '{table_name}':")
for row in rows:
    print(row)

conn.close()