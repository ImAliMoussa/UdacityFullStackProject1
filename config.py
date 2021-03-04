import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True


# Connect to the database
class DatabaseURI:
    # Just change the names of your database and crendtials and all to connect to your local system
    DATABASE_NAME = "fyyur"
    username = 'postgres'
    password = 'changeme'
    url = 'localhost:5432'
    db_dialect = 'postgres'
    SQLALCHEMY_DATABASE_URI = f"{db_dialect}://{username}:{password}@{url}/{DATABASE_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
