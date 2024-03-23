import sqlite3
DB_PATH = "sensible/Dollars.db"

def query(query: str, parameters = ()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, parameters)

    res = None
    if query.strip().startswith("SELECT") and not (" INTO " in query):
        res = cur.fetchall()
    
    conn.commit()
    conn.close()
    return res