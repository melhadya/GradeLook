import os
from dotenv import load_dotenv
from helper import SQL, cp, hp
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
load_dotenv()

def flask_start():
    # DB name and admin credentials    
    global db_name
    db_name = os.getenv("DATABASE")

    # flask initiators
    global app
    app = Flask(__name__)
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
flask_start()

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def check_admin_session():
    if "admin" not in session:
        return False
    return True

def generate_username(name):
    if not name:
        return None
    parts = name.lower().strip().split()
    if len(parts) < 2:
        return parts[0]
    else:
        return parts[0] + "." + parts[-1]

def new_student(sname, birth, sclass, email, phone):
    with SQL(session["db"]) as db:
        scq = f"select * from classes where cname = ?"
        if not db.query(scq, sclass):
            print("Class not found!")
            return False
        squery = f"""
                    insert into students(sname, birth, sclass, email, phone)
                    values(?, ?, ?, ?, ?)
                """
        if session["consumption"] < session["quota"] and db.query(squery, (sname, birth, sclass, email, phone)):
            with SQL(db_name) as tdb:
                iucq = "update users set consumption = ? where id = ?"
                tdb.query(iucq, (session["consumption"]+1, session["id"]))
                session["consumption"] += 1
            return True
    return False

# Admin Routes

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    try:
        session.clear()
        template = "admin_login.html"

        # default
        if request.method == "GET":
            return render_template(template)
        # login
        un = request.form.get("username")
        pw = request.form.get("password")
        aun = os.getenv("ADMIN_USERNAME")
        apw = os.getenv("ADMIN_PASSWORD")
        
        if not un or not pw:
            return render_template(template, error="Must enter username/password!")
        elif not aun or not apw:
            return render_template(template, error="Admin credentials are not set!")
        elif un == aun and pw == apw:
            session["admin"] = "admin"
            return redirect("/admin")
        else:
            return render_template(template, error="Invalid username and/or password!")
    except Exception as e:
        print(f"Error in admin_login: {e}")
        return render_template(template, error="An error occurred during login.")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not check_admin_session():
        return redirect("/login")
    template = "admin.html"

    # show users on admin homepage
    with SQL(db_name) as db:
        get_users = "select * from users"
        users = db.query(get_users)
        if not users:
            return render_template(template, error="No users to show!")
        return render_template(template, users=users)

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not check_admin_session():
        return redirect("/login")
    template = "add_user.html"
    
    # default
    if request.method == "GET":
        return render_template(template)
    
    # adding user
    with SQL(db_name) as db:
        # get data from form
        name = request.form.get("name")
        username = generate_username(name)
        password = username + "GL"
        pw_hash = hp(password)
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        quota = 100
        if not name or not title or not phone or not email:
            return render_template(template, error="Must provide all user data!")
        # add user to db
        auq = """
                insert into users(username, hash, name, title, phone, email, quota)
                values (?, ?, ?, ?, ?, ?, ?)
            """
        db.query(auq, (username, pw_hash, name, title, phone, email, quota))
        # create user db
        uidq = "select id from users where username = ?"
        new_user_id = db.query(uidq, (username,))[0]["id"]
        new_db_name = f"users_db/{new_user_id}.db"
        with SQL(new_db_name) as new_db:
            with open('gl.sql', 'r') as sql_file:
                sql_script = sql_file.read()
            new_db.script(sql_script)
        print("User added successfully!")
    return redirect("/admin")

@app.route("/edit_user", methods=["GET", "POST"])
def edit_user():
    if not check_admin_session():
        return redirect("/login")
    template = "edit_user.html"

    with SQL(db_name) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                print("Cannot get user id!")
                return redirect("/admin")
            user = f"select * from users where id = ?"
            user = db.query(user, (id))[0]
            if not user:
                print("Error getting user data!")
                return redirect("/admin")
            return render_template(template, user=user)    
        # edit user
        id = request.form.get("id")
        name = request.form.get("name")
        username = request.form.get("username")
        pw_hash = hp(username + "GL")
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        quota = int(request.form.get("quota"))
        euq = f"""
                    update users set
                    username = ?,
                    name = ?,
                    hash = ?,
                    title = ?,
                    phone = ?,
                    email = ?,
                    quota = ?
                    where id = ?
                    """
        db.query(euq, (username, name, pw_hash, title, phone, email, quota, id))
    return redirect("/admin")

@app.route("/remove_user")
def remove_user():
    if not check_admin_session():
        return redirect("/login")

    # remove user
    with SQL(db_name) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get user id!")
            return redirect("/admin")
        user = f"delete from users where id = ?"
        db.query(user, id)
        db_path = f"users_db/{id}.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        print("User deleted!")
    return redirect("/admin")

### admin functions done ###

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    template = "login.html"

    # default
    if request.method == "GET":
        return render_template(template)
    
    # login
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return render_template(template, error="Must enter username and password!")
    
    # check password / initiate user session
    with SQL(db_name) as db:
        get_hash = f"select * from users where username = ?"
        user = db.query(get_hash, username)
        if user and cp(user[0]["hash"], password):
            user = user[0]
            session["id"] = user["id"]
            session["name"] = user["name"]
            session["title"] = user["title"]
            session["phone"] = user["phone"]
            session["email"] = user["email"]
            session["quota"] = int(user["quota"])
            session["consumption"] = int(user["consumption"])
            session["db"] = f"users_db/{session["id"]}.db"
            return redirect("/")
    return render_template(template, error="Wrong username/password!")

@app.route("/")
def index():
    if not session:
        return redirect("/login")
    template = "index.html"

    # get classes
    with SQL(session["db"]) as db:
        lcq = "select * from classes"
        classes = db.query(lcq)
        if not classes:
            return render_template(template, error="No classes to show!")
        return render_template(template, classes=classes)
    return render_template(template, error="Can't get classes!")

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if not session:
        return redirect("/login")
    template = "change_password.html"
    
    # default
    if request.method == "GET":
        return render_template(template)
    
    # change password
    old = request.form.get("old")
    new = request.form.get("new")
    confirm = request.form.get("confirm")
    if not old or not new or not confirm:
        return render_template(template, error="Must fill all fields!")
    elif new != confirm:
        return render_template(template, error="Passwords mismatch!")
    
    with SQL(db_name) as db:
        gphq = f"select hash from users where id = ?"
        user = db.query(gphq, session['id'])
        if user and cp(user[0]["hash"], old):
            uhq = f"update users set hash = ? where id = ?"
            db.query(uhq, (hp(new), session["id"]))
            return redirect("/login")
    return render_template(template, error="Wrong password!")

@app.route("/add_class", methods=["GET", "POST"])
def add_class():
    if not session:
        return redirect("/login")
    template = "add_class.html"
    
    # default
    if request.method == "GET":
        return render_template(template)
    
    # add class
    with SQL(session["db"]) as db:
        cname = request.form.get("cname")
        ctype = request.form.get("ctype")
        if not cname or not ctype:
            return render_template(template, error="Must provide class name/type!")
        acq = f"insert into classes(cname, type) values(?, ?)"
        if db.query(acq, (cname, ctype)):
            return redirect("/")
    return render_template(template, error="Class already exists!")
    
@app.route("/edit_class", methods=["GET", "POST"])
def edit_class():
    if not session:
        return redirect("/login")
    template = "edit_class.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                return redirect("/")
            gcq = f"select * from classes where id = ?"
            cdata = db.query(gcq, id)
            if cdata:
                return render_template(template, cdata=cdata[0])
            return render_template(template, error="Can't get class data!")

        # edit class
        id = request.form.get("id")
        cname = request.form.get("cname")
        ctype = request.form.get("ctype")
        if not cname or not ctype or not id:
            return render_template(template, error="Must provide class data!")
        ecq = f"""
                update classes set
                cname = ?,
                ctype = ?
                where cid = ?
                """
        db.query(ecq, (cname, ctype, id))
    return redirect("/")

@app.route("/remove_class")
def remove_class():
    if not session:
        return redirect("/login")
    
    # remove class
    with SQL(session["db"]) as db:
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                print("Cannot get class id!")
                return redirect("/")
            cdq = f"delete from classes where id = ?"
            db.query(cdq, id)
            print("Class deleted!")
    return redirect("/")

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if not session:
        return redirect("/login")
    template = "add_student.html"
    
    if request.method == "GET":
        return render_template(template)
    
    
    # get form data
    if True:
        sname = request.form.get("sname")
        birth = request.form.get("birth")
        sclass = request.form.get("sclass")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not sname or not birth or not email or not phone or not sclass:
            return render_template(template, error="Must provide student data!")
        # add student
        if new_student(sname, birth, sclass, email, phone):
            return redirect("/")
    """else:
        # get students from excel file
        for i in range(10):
            if not new_student(sname, birth, sclass, email, phone):
                print("error adding student" + sname)
        else:
            return redirect("/")
    """
    return render_template(template, error="Error adding student!")
    
@app.route("/edit_student", methods=["GET", "POST"])
def edit_student():
    if not session:
        return redirect("/login")
    template = "edit_student.html"
    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                return redirect("/")
            gsdq = f"select * from students where id = ?"
            sdata = db.query(gsdq, id)
            if sdata:
                return render_template(template, sdata=sdata[0])
            return render_template(template, error="Can't get student data!")
        # edit student
        id = request.form.get("id")
        sname = request.form.get("sname")
        birth = request.form.get("birth")
        sclass = request.form.get("sclass")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not id or not sname or not birth or not email or not phone or not sclass:
            return render_template(template, error="Must provide student data!")
        # sclass_validate
        scvq = f"select * from classes where cname = ?"
        if not db.query(scvq, sclass):
            return render_template(template, error="Class not found!")
        squery = f"""
                    update students set
                    sname = ?,
                    birth = ?,
                    sclass = ?,
                    email = ?,
                    phone = ?
                    where id = ?
                """
        db.query(squery, (sname, birth, sclass, email, phone, id))
        return redirect("/")
    return render_template(template, error="Error editing student!")
    
@app.route("/remove_student")
def remove_student():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                print("Cannot get student id!")
                return redirect("/")
            dsq = f"delete from students where id = ?"
            db.query(dsq, id)
            with SQL(db_name) as tdb:
                ducq = "update users set consumption = ? where id = ?"
                tdb.query(ducq, (session["consumption"]-1, session["id"]))
                session["consumption"] -= 1
            print("Student deleted!")
    return redirect("/")

# add category
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if not session:
        return redirect("/login")
    template = "add_category.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            return render_template(template)
        
        # add category
        cname = request.form.get("cname")
        if not cname:
            return render_template(template, error="Must provide category name!")
        acq = f"insert into categories(catname) values(?)"
        if db.query(acq, (cname)):
            return redirect("/")
    return render_template(template, error="Error adding category!")

# edit category
@app.route("/edit_category", methods=["GET", "POST"])
def edit_category():
    if not session:
        return redirect("/login")
    template = "edit_category.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                return redirect("/")
            gcq = f"select * from categories where id = ?"
            cdata = db.query(gcq, id)
            if cdata:
                return render_template(template, cdata=cdata[0])
            return render_template(template, error="Can't get category data!")

        # edit category
        id = request.form.get("id")
        cname = request.form.get("cname")
        if not cname or not id:
            return render_template(template, error="Must provide category data!")
        ecq = f"""
                update categories set
                catname = ?
                where id = ?
                """
        db.query(ecq, (cname, id))
    return redirect("/")

# remove category
@app.route("/remove_category")
def remove_category():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get category id!")
            return redirect("/")
        dcq = f"delete from categories where id = ?"
        db.query(dcq, id)
        print("Category deleted!")
    return redirect("/")

# add instance
@app.route("/add_instance", methods=["GET", "POST"])
def add_instance():
    if not session:
        return redirect("/login")
    template = "add_instance.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            return render_template(template)
        
        # add instance
        iname = request.form.get("iname")
        iclass = request.form.get("iclass")
        category = request.form.get("category")
        idate = request.form.get("idate")
        if not iname or not iclass or not category or not idate:
            return render_template(template, error="Must provide instance data!")
        # iclass_validate
        icvq = f"select * from classes where cname = ?"
        if not db.query(icvq, iclass):
            return render_template(template, error="Class not found!")
        # icategory_validate
        icvq = f"select * from categories where catname = ?"
        if not db.query(icvq, category):
            return render_template(template, error="Category not found!")
        iquery = f"""
                    insert into instances(iname, iclass, category, idate)
                    values(?, ?, ?, ?)
                """
        if db.query(iquery, (iname, iclass, category, idate)):
            return redirect("/")
    return render_template(template, error="Error adding instance!")

# edit instance
@app.route("/edit_instance", methods=["GET", "POST"])
def edit_instance():
    if not session:
        return redirect("/login")
    template = "edit_instance.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                return redirect("/")
            giq = f"select * from instances where id = ?"
            idata = db.query(giq, id)
            if idata:
                return render_template(template, idata=idata[0])
            return render_template(template, error="Can't get instance data!")

        # edit instance
        id = request.form.get("id")
        iname = request.form.get("iname")
        iclass = request.form.get("iclass")
        category = request.form.get("category")
        idate = request.form.get("idate")
        if not id or not iname or not iclass or not category or not idate:
            return render_template(template, error="Must provide instance data!")
        # iclass_validate
        icvq = f"select * from classes where cname = ?"
        if not db.query(icvq, iclass):
            return render_template(template, error="Class not found!")
        # icategory_validate
        icvq = f"select * from categories where catname = ?"
        if not db.query(icvq, category):
            return render_template(template, error="Category not found!")
        iquery = f"""
                    update instances set
                    iname = ?,
                    iclass = ?,
                    category = ?,
                    idate = ?
                    where id = ?
                """
        db.query(iquery, (iname, iclass, category, idate, id))
    return redirect("/")

# remove instance
@app.route("/remove_instance")
def remove_instance():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get instance id!")
            return redirect("/")
        diq = f"delete from instances where id = ?"
        db.query(diq, id)
        print("Instance deleted!")
    return redirect("/")

# get student report


# get class report


# add students from excel


# add instance from csv