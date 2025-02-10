from helper import SQL, hash, check
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db_name = "gl.db"

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def generate_username(name):
    parts = name.lower().strip().split()
    if len(parts) < 2:
        return parts[0]
    return parts[0] + "." + parts[-1]

### Flask routes/methods ###

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    session.clear()
    template = "admin_login.html"

    if request.method == "GET":
        return render_template(template)
    
    username = request.form.get("username")
    password = request.form.get("username")
    if not username or not password:
        return render_template(template, error="Must enter username and password!")
    
    if username == "gl-admin" and password == "gl-admin":
        session["admin"] = "admin"
        return redirect("/admin")
    
    return render_template(template, error="Invalid username and/or password!")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/login")
    
    db = SQL(db_name)
    try:
        db.connect()
        get_users = "select * from users"
        users = db.query(get_users)
        db.close()
        if not users:
            return render_template("admin.html", error="No users to show!")
    except:
        print("Error collecting users!")
        return render_template("admin.html", error="Error collecting users!")
    return render_template("admin.html", users=users)

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "admin" not in session:
        return redirect("/login")
    
    # add user
    if request.method == "GET":
        return render_template("add_user.html")
    
    db = SQL(db_name)
    try:
        name = request.form.get("name")
        username = generate_username(name)
        password = username + "GL"
        pw_hash = hash(password)
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        quota = 100
        if int(request.form.get("quota")) > 100:
            quota = int(request.form.get("quota"))
        db.connect()
        add_db = f"""
                    insert into users(username, hash, name, title, phone, email, quota)
                    values ('{username}', '{pw_hash}', '{name}', '{title}', '{phone}', '{email}', {quota})
                    """
        db.query(add_db)
        db.close()
        print("User added successfully!")
    except:
        print("Error adding user!")
        return render_template("add_user.html", error="Error adding user!")
    return redirect("/admin")

@app.route("/edit_user", methods=["GET", "POST"])
def edit_user():
    if "admin" not in session:
        return redirect("/login")
    
    # edit user
    db = SQL(db_name)
    if request.method == "GET":
        try:
            user_id = request.args.get("user_id")
            if not user_id:
                print("Cannot get user id!")
                return redirect("/admin")
            db.connect()
            get_user = f"select * from users where id = {user_id}"
            users = db.query(get_user)
            db.close()
            if not users:
                print("Error getting user data!")
                return redirect("/admin")
            return render_template("edit_user.html", user=users[0])
            
        except:
            print("Error getting user data!")
            return redirect("/admin")
    
    try:
        user_id = request.form.get("id")
        name = request.form.get("name")
        username = request.form.get("username")
        password = username + "GL"
        pw_hash = hash(password)
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        quota = 100
        print("QUOTA IS DEFAULT")
        if int(request.form.get("quota")) > 100:
            quota = int(request.form.get("quota"))
            print("QUOTA IS CHANGED")
        
        db.connect()
        update_db = f"""
                    update users set
                    username = '{username}',
                    name = '{name}',
                    hash = '{pw_hash}',
                    title = '{title}',
                    phone = '{phone}',
                    email = '{email}',
                    quota = {quota}
                    where id = {user_id}
                    """
        db.query(update_db)
        db.close()
        print("User edited successfully!")
    except:
        print("Error editing user!")
    return redirect("/admin")

@app.route("/remove_user", methods=["GET", "POST"])
def remove_user():
    if "admin" not in session:
        return redirect("/login")
    
    # remove user
    db = SQL(db_name)
    if request.method == "GET":
        try:
            user_id = request.args.get("user_id")
            if not user_id:
                print("Cannot get user id!")
                return redirect("/admin")
            db.connect()
            user = f"delete from users where id = {user_id}"
            db.query(user)
            db.close()
            print("User deleted!")
        except:
            print("Error deleting user!")
    return redirect("/admin")

### admin functions done ###

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    
    try:
        username = ""   # get un from form
        password = ""   # get pw from form
        if not username or not password:
            return render_template("login.html", error="Must enter username and password!")
    except:
        return render_template("login.html", error="Must enter username and password!")
    
    db = SQL(db_name)
    valid = False
    try:
        db.connect()
        get_hash = "select * from users where username = " + username
        users = db.query(get_hash)
        for user in users:
            valid = check(user["hash"], password)
        db.close()
    except:
        print("Error connecting to DB inside app.py!")
        return redirect("/login")
    
    if valid:
        session["id"] = user["id"]
        session["name"] = user["name"]
        session["title"] = user["title"]
        session["phone"] = user["phone"]
        session["email"] = user["email"]
        session["quota"] = user["quota"]
        return redirect("/")


@app.route("/")
def index():
    if not session:
        return redirect("/login")
    print("DEFINE HOMEPAGE")
    return redirect("/login")