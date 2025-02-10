from argon2 import PasswordHasher as ph
import sqlite3

# DB helper
class SQL:
    def __init__(self, name):
        self.name = name
        self.db = None
    
    def connect(self):
        if self.name is None:
            print("DB error: no db name!")
            return None
        if self.db is not None:
            self.db.close()
        try:
            self.db = sqlite3.connect(self.name)
            self.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print("DB error: can't connect! " + str(e))
            return None
        print("DB connection established!")
    
    def query(self, query):
        
        if self.db is None:
            print("DB error: no db connection!")
            return None

        print("Query: " + query)
        exc = None
        try:
            exc = self.db.cursor().execute(query)
        except sqlite3.Error as e:
            print("DB error: can't execute query! " + str(e))
            return None
        
        print("Query executed!")
        if query.strip().split(" ")[0].lower() == "select":
            return exc.fetchall()
        try:
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print("DB error: can't make changes! " + str(e))
            return False
    
    def close(self):
        if self.db is not None:
            self.db.close()
            print("DB connection closed!")

    def script(self, script):
        
        if self.db is None:
            print("DB error: no db connection!")
            return None

        print("Script: " + script)
        try:
            self.db.cursor().executescript(script)
        except sqlite3.Error as e:
            print("DB error: can't execute query! " + str(e))
            return None
        print("Query executed!")
        try:
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print("DB error: can't make changes! " + str(e))
            return False

# PW hash helper
def hash(password):
    if password:
        return ph().hash(password)
    return None

def check(stored, entered):
    if stored and entered:
        try:
            return ph().verify(stored, entered)
        except:
            return False
    return False

#
