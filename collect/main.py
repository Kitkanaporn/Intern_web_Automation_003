import os
from datetime import datetime

APP_NAME = os.getenv("APP_NAME", "UAT Reminder Test")
LOG_PATH = os.getenv(
    "LOG_PATH",
    "/app/logs/automation_log.txt"
)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

message = (
    f"[{now}] {APP_NAME} "
    "ran successfully from Docker container\n"
)

with open(LOG_PATH, "a", encoding="utf-8") as log_file:
    log_file.write(message)

print(message)