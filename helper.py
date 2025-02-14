from argon2 import PasswordHasher as ph
import sqlite3

# DB helper
class SQL:

    def __init__(self, name):
        self.name = name
        self.db = None

    def __enter__(self):
        db_con = self.connect()
        self.query("PRAGMA foreign_keys=ON")
        return db_con

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print("DB Error: " + str(exc_value))
        self.close()

    def connect(self):
        if self.name is None:
            print("DB error: no db name!")
            return self
        elif self.db is not None:
            self.db.close()
        try:
            self.db = sqlite3.connect(self.name)
            self.db.row_factory = sqlite3.Row
            print("DB connection established!")
        except sqlite3.Error as e:
            print("DB error: can't connect! " + str(e))
            self.db = None
        return self

    def close(self):
        if self.db is not None:
            self.db.close()
            print("DB connection closed!")

    def query(self, query, *args):
        if self.db is None:
            print("DB error: no db connection!")
            return None
        print(query)
        try:
            exc = self.db.cursor()
            exc.execute(query, args)
            print("Query executed!")
            if query.strip().lower().startswith("select"):
                return exc.fetchall()
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print("DB error: can't execute query! " + str(e))
            return None

    def script(self, script):
        if self.db is None:
            print("DB error: no db connection!")
            return None
        print(script)
        try:
            self.db.cursor().executescript(script)
            self.db.commit()
            print("Script executed!")
            return True
        except sqlite3.Error as e:
            print("DB error: can't execute script! " + str(e))
            return None

# PW hash helper
def hp(password):
    if password:
        return ph().hash(password)
    return None

def cp(stored, entered):
    if stored and entered:
        try:
            return ph().verify(stored, entered)
        except Exception as e:
            print("Error verifying password: " + str(e))
    return False

# END