# GradeLook (GL)
### Video Demo: https://youtu.be/AE7coNR_EDw

## Description:

GradeLook is a grade management system designed to help educators track academic performance of their students. With GradeLook, users can easily input, manage, and view grades. The system offers features such as grade calculation, and customizable reporting.

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
    git clone https://github.com/melhadya/GL.git
    cd GL
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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For further queries, please contact [melhady.a@gmail.com] or WhatsApp [+201094650546].