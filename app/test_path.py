import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Get the project root directory
project_root = Path(__file__).resolve().parent
creds_file_name = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE")

# Construct the full path to the credentials file
if "/" in creds_file_name:
    creds_path = project_root / creds_file_name
else:
    creds_path = project_root / "app" / "credentials" / creds_file_name

print(f"Project root: {project_root}")
print(f"Credentials file path: {creds_path}")
print(f"File exists: {creds_path.exists()}")