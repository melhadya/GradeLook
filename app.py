import os
import csv
from dotenv import load_dotenv
from helper import SQL, cp, hp
from flask import Flask, redirect, render_template, request, session, send_file, after_this_request
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
        if available and db.query(student_q, name, class_id, email, phone):
            # student added
            update_consumption()
            return True
    return False
def allowed_file(name):
    ALLOWED_EXTENSIONS = {'csv'}
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def rec_update(id, score):
    with SQL(session["db"]) as db:
        update_q = "update records set score = ? where id = ?"
        db.query(update_q, score, id)
        print("Record updated!")
        return True
    return False

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
        if db.query(add_q, username, pw_hash, name, title, phone, email):
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
            print("Error editing user!")
            return redirect("/edit_user?id="+str(id))
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
                print("No class id!")
                return redirect("/classes")
            class_q = "select * from classes where id = ?"
            class_data = db.query(class_q, id)
            if class_data:
                return render_template(template, class_data=class_data[0])
            print("Can't get class data")
            return redirect("/classes")

        # edit class
        id = request.form.get("id")
        name = request.form.get("name")
        type = request.form.get("type")
        if not name or not type or not id:
            print("Must provide class data!")
            return redirect("/edit_class?id="+str(id))
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
        if db.query(delete_q, id):
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
        if not id:
            print("No class id!")
            return redirect("/classes")
        inst_q = "select instances.*, categories.name as category_name from instances, categories where instances.class = ? and instances.category=categories.id"
        instances = db.query(inst_q, id)
        class_q = """
            select id, name, type, (
            select count(name) from students where class = classes.id
            ) as students_count
            from classes where id = ?
            """
        class_data = db.query(class_q, id)
        if not class_data:
            print("Class not found!")
            return redirect("/classes")
        if instances:
            return render_template(template, instances=instances, class_data=class_data[0])
    return render_template(template, error="No instances to show!", class_data=class_data[0])

@app.route("/students")
def students():
    if not session:
        return redirect("/login")
    
    template = "students.html"
    class_id = request.args.get("class")

    with SQL(session["db"]) as db:
        # If no specific class is selected, display all students with their class names
        if not class_id:
            students_q = """SELECT students.*, classes.name as class_name
                     FROM students, classes
                     where students.class = classes.id"""
            students = db.query(students_q)
            if students:
                return render_template(template, students=students)
            else:
                return render_template(template, error="No students to show!")
        # If a specific class is selected, display students from that class
        students_q = """SELECT students.*, classes.name as class_name
                 FROM students, classes
                 where students.class = classes.id and
                 students.class = ?"""
        students = db.query(students_q, class_id)
        if students:
            selected_class = students[0]["class_name"]
            return render_template(template, students=students, selected_class=selected_class)
        else:
            print("No students in class!")
            return redirect("/view_class?id="+str(class_id))
    return redirect("/students")

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if not session:
        return redirect("/login")
    template = "add_student.html"
    
    student_class = None
    if request.method == "GET":
        student_class = request.args.get("class")
        if not student_class:
            print("No class found for adding student!")
            return redirect("/classes")
        with SQL(session["db"]) as db:
            class_q = "select id, name from classes where id = ?"
            class_data = db.query(class_q, student_class)
            if class_data:
                return render_template(template, class_data=class_data[0])
            print("Class not found for adding student!")
            return redirect("/classes")
    
    # get form data
    student_class = request.form.get("class")
    if not student_class:
        print("Class not found for adding student!")
        return redirect("/classes")
    if 'file' not in request.files:
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not name or not email or not phone:
            print("Must provide student data!")
            return redirect("/add_student?class="+str(student_class))
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
                    if not new_student(s["Name"], student_class, s["Email"], s["Phone"]):
                        print(f"Student {s['Name']} not added")
                os.remove(fpath)
                update_consumption()
                return redirect("/students?class="+str(student_class))
        print("Error adding file!")
    print("Error adding student/s!")
    return redirect("/view_class?id="+str(student_class))
        
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
                print("Error getting student id!")
                return redirect("/students")
            
            student_q = "select * from students where id = ?"
            student_data = db.query(student_q, id)
            if student_data:
                return render_template(template, student_data=student_data[0])
            
            print("Can't get student data!")
            return redirect("/students")
        
        # edit student
        id = request.form.get("id")
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not id or not name or not email or not phone:
            print("Must provide student data!")
            return redirect("/students")
        
        student_q = """
                    update students set
                    name = ?,
                    email = ?,
                    phone = ?
                    where id = ?
                """
        if db.query(student_q, name, email, phone, id):
            print("Student edited successfully!")
    print("Error editing student!")
    return redirect("/students")
    
@app.route("/remove_student")
def remove_student():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get student id!")
            return redirect("/students")
        delete_q = "delete from students where id = ?"
        if db.query(delete_q, id):
            update_consumption()
            print("Student deleted!")
    return redirect("/students")

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
        share = int(request.form.get("share"))/100
        if not name or not share:
            return render_template(template, error="Must provide category name/%!")
        add_q = "insert into categories(name, share) values(?, ?)"
        if db.query(add_q, name, share):
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
                print("Can't get category id")
                return redirect("/categories")
            cat_q = "select * from categories where id = ?"
            cats = db.query(cat_q, id)
            if cats:
                return render_template(template, cat=cats[0])
            print("Can't get category data")
            return redirect("/categories")

        # edit category
        id = request.form.get("id")
        name = request.form.get("name")
        share = int(request.form.get("share"))/100
        if not name or not id:
            print("Must provide category data!")
            return redirect("/categories")
        update_q = """
                update categories set
                name = ?, share = ?
                where id = ?
                """
        db.query(update_q, name, share, id)
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
        if db.query(delete_q, id):
            print("Category deleted!")
    return redirect("/categories")

@app.route("/add_instance", methods=["GET", "POST"])
def add_instance():
    if not session:
        return redirect("/login")
    template = "add_instance.html"

    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            classes_q = "select * from classes"
            classes_data = db.query(classes_q)
            
            cat_q = "select * from categories"
            cats = db.query(cat_q)
            
            if not classes_data or not cats:
                print("Can't get classes/categories")
                return redirect("/classes")
            return render_template(template, classes_data=classes_data, cats=cats)
        
        # add instance
        title = request.form.get("title")
        classes_id = request.form.getlist("classes")
        category = request.form.get("category")
        date = request.form.get("date")
        total = request.form.get("total")
        if not title or not classes_id or not category or not date:
            print("Must provide instance data!")
            return redirect("/add_instance")
        
        for class_id in classes_id:
            # add instance
            inst_q = """
                        insert into instances(title, class, category, date, total)
                        values(?, ?, ?, ?, ?)
                    """
            db.query(inst_q, title, class_id, category, date, total)
            instid_q = "select id from instances order by id desc limit 1"
            inst_id = db.query(instid_q)[0]["id"]
            students_q = "select id from students where class = ?"
            students_ids = db.query(students_q, class_id)
            for student in students_ids:
                record_q = "insert into records(instance, student) values(?, ?)"
                db.query(record_q, inst_id, student["id"])
        else:
            print("Instance added!")
            return redirect("/classes")        
    print("Error adding instance!")
    return redirect("/add_instance")

@app.route("/remove_instance")
def remove_instance():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Cannot get instance id!")
            return redirect("/classes")
        delete_q = "delete from instances where id = ?"
        if db.query(delete_q, id):
            print("Instance deleted!")
    return redirect("/classes")

@app.route("/view_instance")
def view_instance():
    if not session:
        return redirect("/login")
    template = "view_instance.html"

    with SQL(session["db"]) as db:
        id = request.args.get("id")
        if not id:
            print("Can't get instance id!")
            return redirect("/classes")
        inst_q = """
                select instances.*, categories.name as catname, classes.name as class_name
                from instances, categories, classes where categories.id = instances.category and instances.class = classes.id
                and instances.id = ?
                """
        instances = db.query(inst_q, id)
        cats_q = "select id, name from categories"
        cats = db.query(cats_q)
        records_q = """
                    select records.id, records.score, students.name from records, students
                    where instance = ? and students.id = records.student
                    """
        records = db.query(records_q, id)
        if not instances or not cats or not records:
            print("Error getting instance/records/categories data!")
            return redirect("/classes")
        return render_template(template, inst=instances[0], cats=cats, records=records)

@app.route("/edit_instance", methods=["GET", "POST"])
def edit_instance():
    if not session:
        return redirect("/login")
    
    with SQL(session["db"]) as db:
        # default
        if request.method == "GET":
            return redirect("/classes")
        
        # edit instance
        id = request.form.get("id")
        title = request.form.get("title")
        category = request.form.get("category")
        date = request.form.get("date")
        total = request.form.get("total")
        old_total = request.form.get("old_total")
        if not id or not title or not category or not date or not total:
            print("Must provide instance data!")
            return redirect("/view_instance?id="+str(id))
        update_q = """
                update instances set
                title = ?,
                category = ?,
                date = ?,
                total = ?
                where id = ?;
                """
        db.query(update_q, title, category, date, total, id)
        if not total == old_total:
            update_q = """
                update records set score = 0 where instance = ?;
                """
        db.query(update_q, id)
        print("Instance Edited!")
    return redirect("/view_instance?id="+str(id))

@app.route("/update_records", methods=["GET", "POST"])
def update_records():
    if not session:
        return redirect("/login")
    
    if request.method == "GET":
        return redirect("/classes")
    
    # get form data
    instance = request.form.get("instance")
    if not instance:
        print("No instance found!")
        return redirect("/classes")
    if 'file' not in request.files:
        with SQL(session["db"]) as db:
            records = db.query("select records.id, instances.total from records, instances where records.instance = ? and records.instance = instances.id", instance)
            for record in records:
                score = int(request.form.get("score"+str(record["id"])))
                if not score:
                    print("Must provide all scores! Error record " + str(record["id"]))
                elif score <= record["total"] and rec_update(record["id"], score):
                    print("Record updated!")
                else:
                    print("Score exceeds total! Error record " + str(record["id"]))
            return redirect("/view_instance?id="+str(instance))
    else:
        file = request.files["file"]
        if file and not file.filename == '' and allowed_file(file.filename):
            fpath = 'temp_files/' + str(file.filename)
            file.save(fpath)
            with open(fpath) as f:
                records = csv.DictReader(f)
                total = None
                with SQL(session["db"]) as db:
                    total = db.query("select total from instances where id = ?", instance)[0]["total"]
                for record in records:
                    id = record["ID"]
                    score = int(str(record["Score"]))
                    if not score:
                        print("Must provide all scores! Error record " + str(id))
                    elif score <= total and rec_update(id, score):
                        print("Record updated!")
                    else:
                        print("Score exceeds total! Error record " + str(id))
                os.remove(fpath)
                return redirect("/view_instance?id="+str(instance))
        print("Error adding file!")
    return redirect("/view_instance?id="+str(instance))

#######################

def get_student_report(student_id):
    report = []
    ind = {"ID":0, "Category": "", "Score":0.0, "Count":0, "Total":0, "From":0}
    with SQL(session["db"]) as db:
        
        # get categories and prepare report
        cats_q = "SELECT * FROM categories"
        cats = db.query(cats_q)
        for cat in cats:
            n = ind.copy()
            n["ID"] = int(cat["id"])
            n["Category"] = str(cat["name"])
            n["From"] = int(cat["share"]*100)
            report.append(n)
        
        records_q = """
            SELECT records.score, instances.total, instances.category as cat_id
            FROM records
            JOIN instances ON records.instance = instances.id
            WHERE records.student = ?
        """
        records = db.query(records_q, student_id)
        if not records:
            return None
        for record in records:
            for i in range(len(report)):
                if int(record["cat_id"]) == report[i]["ID"]:
                    report[i]["Score"] += float(record["score"]) / int(record["total"])
                    report[i]["Count"] += 1
        
        ln = ind.copy()
        ln["Category"] = "Final Grade"
        ln["From"] = 100
        ln["Count"] = 1
        for i in range(len(report)):
            if report[i]["Count"] > 0:
                report[i]["Total"] = round(report[i]["Score"] / report[i]["Count"] * report[i]["From"],1)
                ln["Total"] += report[i]["Total"]
        report.append(ln)

        for i in report:
            del i["ID"]
            del i["Score"]
            del i["Count"]
    
        student_name = db.query("select name from students where id = ?", student_id)[0]["name"]
    return [student_id, student_name, report]

@app.route("/student_report")
def student_report():
    if not session:
        return redirect("/login")
    template = "student_report.html"
    student_id = request.args.get("id")
    if not student_id:
        print("No student id provided!")
        return redirect("/students")
    
    records_q = """
                    select records.id, records.score,
                    instances.id as instance, instances.total, instances.title, instances.date,
                    classes.name as class, classes.id as class_id,
                    students.name, students.phone,
                    categories.name as cat
                    from records, instances, classes, students, categories
                    where students.id = ?
                    and records.student = students.id
                    and records.instance = instances.id
                    and instances.class = classes.id
                    and instances.category = categories.id
                    order by instances.date
                    """
    with SQL(session["db"]) as db:
        records = db.query(records_q, student_id)
        if records:
            return render_template(template, records=records, head=records[0])
    return render_template(template, error="No records to show!")

@app.route("/class_report")
def class_report():
    if not session:
        return redirect("/login")
    
    class_id = request.args.get("id")
    if not class_id:
        print("No class id provided!")
        return redirect("/classes")
    
    head = ["ID", "Name"]
    table = []
    reports = []
    with SQL(session["db"]) as db:
        students_q = "select id from students where class = ?"
        students_ids = db.query(students_q, class_id)
        for i, id in enumerate(students_ids):
            report = get_student_report(id["id"])
            if report:
                table.append([id["id"], report[1]])
                reports.append(report[2])
    
    if reports:
        for cat in reports[0]:
            head.append(str(cat["Category"])+' ('+str(cat["From"])+')')

        for i, report in enumerate(reports):
            table[i].extend([str(cat["Total"]) for cat in report])
        
    fpath = f"temp_files/class{class_id}.csv"
    with open(fpath, 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(head)
        wr.writerows(table)

    import glob
    from xlsxwriter.workbook import Workbook
    npath = ''
    for csvfile in glob.glob(fpath):
        npath = csvfile[:-4] + '.xlsx'
        wb = Workbook(npath)
        worksheet = wb.add_worksheet()
        with open(csvfile, 'rt', encoding='utf8') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):
                    worksheet.write(r, c, col)
        wb.close()

    @after_this_request
    def remove_file(response):
        try:
            os.remove(fpath)
            os.remove(npath)
        except Exception as error:
            print(f"Error deleting file: {error}")
        return response

    return send_file(npath, as_attachment=True)
