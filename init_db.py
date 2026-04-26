
import sys
import os

# Add parent directory to path to import former module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from former.backend.db import init_db
from former.backend.users import init_db_and_default_user


if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db_and_default_user()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)
