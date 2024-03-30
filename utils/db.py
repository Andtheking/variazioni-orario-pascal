import sqlite3
from .jsonUtils import fromJSONFile

DB_PATH = fromJSONFile("sensible/utils.json")['db_path']




def queryGet(query: str, parameters = ()):
    def x(cur: sqlite3.Cursor):
        res = None
        res = cur.fetchall()
        return res
    return connection(query, parameters, x)

def queryNoReturn(query: str, parameters = ()):
    return connection(query, parameters)

def queryGetSingleValue(query: str, parameters = ()):
    def x(cur: sqlite3.Cursor):
        res = None
        res = cur.fetchall()[0][0]
        return res
    return connection(query, parameters, x)

def connection(query: str, parameters = (), method = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, parameters)
    
    res = None
    if method is not None:
        res = method(cur)
    
    conn.commit()
    conn.close()
    
    return res

if __name__ == '__main__':
    user = {}
    user['id'] = 245996916
    
    print(queryGetSingleValue("""--sql
        SELECT COUNT(*) 
        FROM utenti
        WHERE id = ? AND modalita = 'studente';
    """,(user['id'],)))