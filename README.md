# GradeLook (GL)
### Video Demo: https://youtu.be/AE7coNR_EDw

## Description:

GradeLook is a comprehensive grade management system designed to assist educators in tracking and managing the academic performance of their students. This system provides a user-friendly interface that allows educators to easily input, manage, and view grades. GradeLook is equipped with a variety of features aimed at simplifying the grading process and enhancing the overall efficiency of academic performance tracking.
With GradeLook, users can perform a wide range of tasks including user management, class management, student management, and grade management. The system also offers customizable reporting features, enabling educators to generate detailed reports based on various criteria. These reports can be tailored to meet specific needs, providing valuable insights into student performance and helping educators make informed decisions.

GradeLook is built using Python and Flask, ensuring a robust and scalable application. The system uses SQLite for database management, providing a lightweight and efficient solution for storing and retrieving data. The application also incorporates HTML and CSS for a clean and intuitive user interface.

Whether you are an individual educator or part of an educational institution, GradeLook is designed to streamline your grading process and provide you with the tools you need to effectively manage and analyze student performance.

## Features

- **User Management**: Admins can add, edit, and remove users.
- **Class Management**: Add, edit, and remove classes.
- **Student Management**: Add, edit, and remove students.
- **Grade Management**: Input and manage grades for students.
- **Customizable Reporting**: Generate and customize reports based on various criteria.

## Prerequisites

- Python
- Flask
- SQLite

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/melhadya/GradeLook.git
    cd GradeLook
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the environment variables:
    Create a `.env` file in the root directory and add the following:
    ```env
    ADMIN_USERNAME=admin_default_username
    ADMIN_PASSWORD=admin_default_password
    USER_PASSWORD=new_user_default_password
    DATABASE=admin_database
    ```

## Usage

1. Run the Flask application:
    ```sh
    flask run --debug
    ```

2. Open your web browser and go to `http://127.0.0.1:5000`.

## Technologies Used

- Python
- Flask
- SQLite
- HTML/CSS

## Project Files/Folders

- `.env`: Admin defaults.
- `app.py`: Main Flask application file containing routes and logic.
- `helper.py`: Helper functions for database operations and password hashing.
- `gl.sql`: SQL script to set up the database schema for each new user.
- `static/`: Contains app icon and editable css styles.
- `templates/`: Contains app HTML templates.
- `users_db/`: Used to store users databases.
- `temp_files/`: Used to store temp csv/excel files.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## Contact

For further queries, please contact [melhady.a@gmail.com] or WhatsApp [+201094650546].