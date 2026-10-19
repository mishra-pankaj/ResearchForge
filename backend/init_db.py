# backend/init_db.py
from backend.db import engine, Base
from backend import models  # noqa: F401  (importing registers the table)


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    main()