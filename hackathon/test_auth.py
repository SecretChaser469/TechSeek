import traceback
import sys
from backend.app.seed import seed_db

try:
    print("Running seed_db()...")
    seed_db()
    print("Seed completed successfully!")
except Exception as e:
    with open("traceback_error.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    print("Traceback written to traceback_error.txt")


