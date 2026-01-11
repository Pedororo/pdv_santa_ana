import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABAASE_URL", "sqlite:///pdv.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

