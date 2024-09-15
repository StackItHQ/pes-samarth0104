import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import time
import hashlib
import threading  # Import threading to implement mutex locking

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Create a global mutex lock
lock = threading.Lock()


def google_sheets_auth():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def read_spreadsheet_id():
    if not os.path.exists("spreadsheet_id.txt"):
        raise FileNotFoundError("The spreadsheet ID file is missing.")
    with open("spreadsheet_id.txt", "r") as file:
        return file.read().strip()


def fetch_from_mysql():
    """Fetch all data from the MySQL table."""
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        # Fetch all records from the internships table
        cursor.execute(
            "SELECT id, company_name, job_title, cgpa_cutoff, remarks FROM internships"
        )
        records = cursor.fetchall()

        return records

    except mysql.connector.Error as error:
        print(f"Failed to read data from MySQL table {error}")
        return []

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def update_google_sheet(data):
    """Update Google Sheet with the data fetched from MySQL."""
    creds = google_sheets_auth()
    service = build("sheets", "v4", credentials=creds)

    spreadsheet_id = read_spreadsheet_id()
    sheet = service.spreadsheets()

    # Clear the sheet below the header row (from A2 onward)
    clear_range = "Sheet1!A2:Z1000"
    sheet.values().clear(spreadsheetId=spreadsheet_id, range=clear_range).execute()

    # Prepare the data to be inserted into Google Sheets
    values = [
        ["ID", "Company Name", "Job Title", "CGPA \nCut-off", "Remarks"]
    ]  # Keep headers
    values += data  # Add the fetched MySQL data

    body = {"values": values}

    # Write data to the sheet starting from A2 (this ensures the headers stay in place)
    result = (
        sheet.values()
        .update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A2",
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )

    print(f"{result.get('updatedCells')} cells updated.")


def calculate_data_hash(data):
    """Calculate a hash for the MySQL data to detect changes efficiently."""
    hash_md5 = hashlib.md5()
    for row in data:
        row_string = "".join(map(str, row))  # Convert each row to a string
        hash_md5.update(row_string.encode("utf-8"))
    return hash_md5.hexdigest()


def poll_and_sync_event_based():
    last_data_hash = ""  # Initialize with an empty hash

    while True:
        # Acquire the mutex lock before fetching and syncing data
        with lock:
            print("Lock acquired. Checking for database changes...")

            # Fetch the current data from MySQL
            current_db_data = fetch_from_mysql()

            # Calculate the hash of the new data
            new_data_hash = calculate_data_hash(current_db_data)

            # Check if the new hash is different from the last hash (indicating changes)
            if new_data_hash != last_data_hash:
                print("Changes detected in the database. Syncing with Google Sheets...")
                # If changes are detected, update Google Sheets
                update_google_sheet(current_db_data)
                last_data_hash = new_data_hash  # Update the last data hash
            else:
                print("No changes detected in the database.")

        # Release the lock after the critical section is completed
        print("Lock released. Sleeping before the next poll.")
        time.sleep(10)  # Poll every 10 seconds (adjust as needed)


if __name__ == "__main__":
    poll_and_sync_event_based()
