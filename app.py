import os
import csv
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

# helper functions
def check_admin_session():
    if "admin" not in session:
        return False
    return True
def generate_username(name):
    # check for input
    if not name:
        return None
    # divide name into parts
    parts = name.lower().strip().split(" ")
    # set un to 1st two letters if one part
    if len(parts) < 2:
        return parts[0][0:2]
    # set un to 1st+last parts 1st letters
    else:
        return parts[0][0] + "." + parts[-1][0]
def update_consumption():
    with SQL(session["db"]) as db:
        q = "select count(id) as students_count from students"
        count = db.query(q)[0]["students_count"]
        session["consumption"] = count
    with SQL(db_name) as db:
        q = "update users set consumption = ? where id = ?"
        if db.query(q, session["consumption"], session["id"]):
            return True
def new_student(name, class_id, email, phone):
    with SQL(session["db"]) as db:
        # check class
        clas_q = "select * from classes where id = ?"
        if not db.query(clas_q, class_id):
            print("Class not found!")
            return False
        # check quota availability
        available = session["consumption"] < session["quota"]
        # add student
        student_q = """
                        insert into students(name, class, email, phone)
                        values(?, ?, ?, ?)
                        """
        if available and db.query(student_q, name, clas, email, phone):
            # student added
            update_cons("inc")
            return True
    return False
def allowed_file(name):
    ALLOWED_EXTENSIONS = {'csv'}
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin Routes

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    try:
        session.clear()
        template = "ad_admin_login.html"
        
        # default
        if request.method == "GET":
            return render_template(template)
        
        # login method
        un = request.form.get("username")
        pw = request.form.get("password")
        aun = os.getenv("ADMIN_USERNAME")
        apw = os.getenv("ADMIN_PASSWORD")
        
        # check credentials
        if un and pw and aun and apw and un == aun and pw == apw:
            session["admin"] = "admin"
        
        return redirect("/admin")
    
    except Exception as e:
        print(f"Error in admin_login: {e}")
        return render_template(template, error="An error occurred during login.")
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not check_admin_session():
        return redirect("/login")
    template = "ad_admin.html"

    # show users on admin homepage
    with SQL(db_name) as db:
        users_q = "select * from users"
        users = db.query(users_q)
        if not users:
            return render_template(template, error="No users to show!")
        return render_template(template, users=users)
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not check_admin_session():
        return redirect("/login")
    template = "ad_add_user.html"
    
    # default
    if request.method == "GET":
        return render_template(template)
    
    # adding user
    with SQL(db_name) as db:
        
        # get data from form
        name = request.form.get("name")
        username = generate_username(name)
        pw_hash = hp(os.getenv("USER_PASSWORD"))
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        if not name or not title or not phone or not email:
            return render_template(template, error="Must provide all user data!")
        
        # add user to db
        add_q = """
                insert into users(username, hash, name, title, phone, email)
                values (?, ?, ?, ?, ?, ?)
            """
        if db.query(add_q, username, pw_hash, name, title, phone, email)
            # create user db
            id_q = "select id from users where username = ?"
            new_user_id = db.query(id_q, username)[0]["id"]
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
    template = "ad_edit_user.html"

    with SQL(db_name) as db:
        # default
        if request.method == "GET":
            id = request.args.get("id")
            if not id:
                print("Cannot get user id!")
                return redirect("/admin")
            user_q = "select * from users where id = ?"
            user = db.query(user_q, id)[0]
            if not user:
                print("Error getting user data!")
                return redirect("/admin")
            return render_template(template, user=user)    
        
        # edit user
        id = request.form.get("id")
        name = request.form.get("name")
        username = request.form.get("username")
        pw_hash = hp(os.getenv("USER_PASSWORD"))
        title = request.form.get("title")
        phone = request.form.get("phone")
        email = request.form.get("email")
        quota = int(request.form.get("quota"))
        edit_q = """
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
        if not db.query(edit_q, username, name, pw_hash, title, phone, email, quota, id):
            return render_template(template, error="Error editing user!")
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
        user_q = "delete from users where id = ?"
        db.query(user_q, id)
        # delete user db
        db_path = f"users_db/{id}.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        print("User deleted!")
    return redirect("/admin")

# Admin Routes Done

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
        hash_q = "select * from users where username = ?"
        user = db.query(hash_q, username)
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
    return redirect("/classes")

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
        hash_q = "select hash from users where id = ?"
        old_hash = db.query(hash_q, session['id'])
        if old_hash and cp(old_hash[0]["hash"], old):
            update_q = "update users set hash = ? where id = ?"
            db.query(update_q, hp(new), session["id"])
            return redirect("/login")
    return render_template(template, error="Wrong password!")

@app.route("/classes")
def classes():
    if not session:
        return redirect("/login")
    template = "classes.html"

    # get classes
    with SQL(session["db"]) as db:
        classes_q = """
            select id, name, type, (
            select count(name) from students where class = classes.id
            ) as students_count
            from classes
            """
        classes = db.query(classes_q)
        if not classes:
            return render_template(template, error="No classes to show!")
        return render_template(template, classes=classes)
    return render_template(template, error="Can't get classes!")

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
        name = request.form.get("name")
        type = request.form.get("type")
        if not name or not type:
            return render_template(template, error="Must provide class name/type!")
        add_q = "insert into classes(name, type) values(?, ?)"
        if db.query(add_q, name, type):
            return redirect("/classes")
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
                return redirect("/classes")
            class_q = "select * from classes where id = ?"
            class_data = db.query(class_q, id)
            if class_data:
                return render_template(template, class_data=class_data[0])
            return render_template(template, error="Can't get class data!", class_data=None)

        # edit class
        id = request.form.get("id")
        name = request.form.get("name")
        type = request.form.get("type")
        if not name or not type or not id:
            return render_template(template, error="Must provide class data!", class_data=None)
        update_q = """
                update classes set
                name = ?,
                type = ?
                where id = ?
                """
        db.query(update_q, name, type, id)
    return redirect("/classes")

@app.route("/remove_class")
def remove_class():
    if not session:
        return redirect("/login")
    
    # remove class
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get class id!")
            return redirect("/classes")
        delete_q = "delete from classes where id = ?"
        db.query(delete_q, id)
        print("Class deleted!")
        update_consumption()
    return redirect("/classes")

@app.route("/view_class")
def view_class():
    if not session:
        return redirect("/login")
    template = "view_class.html"
    
    class_data = None
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        inst_q = "select * from instances where class = ?"
        instances = db.query(inst_q, id)
        class_q = "select * from classes where id = ?"
        class_data = db.query(class_q, id)[0]
        if instances:
            return render_template(template, instances=instances, class_data=class_data)
    return render_template(template, error="No instances to show!", class_data=class_data)

@app.route("/students")
def students():
    if not session:
        return redirect("/login")
    
    template = "students.html"
    class_id = request.args.get("class")

    with SQL(session["db"]) as db:
        # If no specific class is selected, display all students with their class names
        if not class_id:
            students_q = """SELECT students.*, classes.name 
                     FROM students, classes
                     where students.class = classes.id"""
            students = db.query(students_q)
            return render_template(template, students=students, selected_class=None)
        
        # If a specific class is selected, display students from that class
        students_q = """SELECT students.*, classes.name 
                 FROM students
                 JOIN classes ON students.class = classes.id
                 WHERE students.class = ?"""
        students = db.query(students_q, class_id)
        
        class_q = "SELECT cname, id FROM classes WHERE id = ?"
        selected_class = db.query(class_q, class_id)[0]
        
        if students and selected_class:
            return render_template(template, students=students, selected_class=selected_class)
        
        return render_template(template, selected_class=selected_class, error="No students to show!")
    
    return redirect("/students")

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if not session:
        return redirect("/login")
    template = "add_student.html"
    
    student_class = None
    if request.method == "GET":
        student_class = request.args.get("class")
        with SQL(session["db"]) as db:
            class_q = "select id, name from classes where id = ?"
            class_data = db.query(class_q, student_class)[0]
        return render_template(template, class_data=class_data)
    
    # get form data
    student_class = request.form.get("class")
    if 'file' not in request.files:
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not name or not email or not phone or not student_class:
            return render_template(template, error="Must provide student data!", class_data=None)
        # add student
        if new_student(name, student_class, email, phone):
            update_consumption()
            return redirect("/students?class="+str(student_class))
    else:
        file = request.files["file"]
        if file and not file.filename == '' and allowed_file(file.filename):
            fpath = 'temp_files/' + str(file.filename)
            file.save(fpath)
            with open(fpath) as f:
                data = csv.DictReader(f)
                for s in data:
                    if not new_student(s["name"], student_class, s["email"], s["phone"]):
                        print(f"Student {s['name']} not added")
                os.remove(fpath)
                update_consumption()
                return redirect("/students?class="+str(student_class))

    return render_template(template, error="Error adding student!", class_data=None)
    
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
            student_q = "select * from students where id = ?"
            student_data = db.query(student_q, id)
            if student_data:
                return render_template(template, student_data=student_data[0])
            return render_template(template, error="Can't get student data!", student_data=None)
        
        # edit student
        id = request.form.get("id")
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not id or not name or not email or not phone:
            return render_template(template, error="Must provide student data!", student_data=None)
        student_q = """
                    update students set
                    name = ?,
                    email = ?,
                    phone = ?
                    where id = ?
                """
        db.query(student_q, name, email, phone, id)
        class_q = "select class from students where id = ?"
        class_id = db.query(class_q, id)[0]["class"]
        return redirect("/students?class="+str(class_id))
    return render_template(template, error="Error editing student!", student_data=None)
    
@app.route("/remove_student")
def remove_student():
    if not session:
        return redirect("/login")
    
    class_id = None
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get student id!")
            return redirect("/students")
        class_q = "select class from students where id = ?"
        class_id = db.query(class_q, id)[0]["class"]
        delete_q = "delete from students where id = ?"
        if db.query(delete_q, id):
            update_consumption()
            print("Student deleted!")
    return redirect("/students?class="+str(class_id))

@app.route("/categories")
def categories():
    if not session:
        return redirect("/login")
    template = "categories.html"

    with SQL(session["db"]) as db:
        cat_q = "select * from categories"
        cats = db.query(cat_q)
        if cats:
            return render_template(template, cats=cats)
    return render_template(template, error="No categories to show!")

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
        name = request.form.get("name")
        if not name:
            return render_template(template, error="Must provide category name!")
        add_q = "insert into categories(name) values(?)"
        if db.query(add_q, name):
            return redirect("/categories")
    return render_template(template, error="Error adding category!")

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
                return redirect("/categories")
            cat_q = "select * from categories where id = ?"
            cats = db.query(cat_q, id)
            if cats:
                return render_template(template, cat=cats[0])
            return render_template(template, error="Can't get category data!", cat=None)

        # edit category
        id = request.form.get("id")
        name = request.form.get("name")
        if not name or not id:
            return render_template(template, error="Must provide category data!", cat=None)
        update_q = f"""
                update categories set
                name = ?
                where id = ?
                """
        db.query(update_q, name, id)
    return redirect("/categories")

@app.route("/remove_category")
def remove_category():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get category id!")
            return redirect("/categories")
        delete_q = "delete from categories where id = ?"
        db.query(delete_q, id)
        print("Category deleted!")
    return redirect("/categories")

###################################################3
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
        if db.query(iquery, iname, iclass, category, idate):
            giq = f"select id from instances order by id desc limit 1"
            ni = "inst" + str(db.query(giq)[0]["id"])
            iit = f"""
                create table {ni}(
                id integer primary key,
                student integer not null,
                score numeric default 0,
                total numeric not null,
                foreign key(student) references students(id) on delete cascade on update cascade)
                """
            db.script(iit)
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
        db.query(iquery, iname, iclass, category, idate, id)
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

# add instance data from csv file
# add students to a class from csv file
# get student report
# get class grades report for all instances for every student