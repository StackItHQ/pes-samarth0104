import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import hashlib
import threading
import time
import sys
import msvcrt  # For detecting keypress on Windows

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Create a global mutex lock
lock = threading.Lock()

# A global flag to signal threads to exit gracefully
exit_flag = False


# Google Sheets Authentication
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


# ===================== DB to Sheets Sync ===================== #
def fetch_from_mysql():
    """Fetch all data from the MySQL table."""
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

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

    clear_range = "Sheet1!A2:Z1000"
    sheet.values().clear(spreadsheetId=spreadsheet_id, range=clear_range).execute()

    values = [["ID", "Company Name", "Job Title", "CGPA \nCut-off", "Remarks"]]
    values += data

    body = {"values": values}
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


def db_to_sheets_sync():
    """Synchronize data from MySQL to Google Sheets."""
    last_data_hash = ""  # Initialize with an empty hash

    while not exit_flag:  # Exit if the flag is set to True
        current_db_data = fetch_from_mysql()
        new_data_hash = calculate_data_hash(current_db_data)

        if new_data_hash != last_data_hash:
            # Only acquire the lock if a change is detected
            if lock.acquire(blocking=False):
                try:
                    print("Lock acquired for DB to Sheets Sync.")
                    print("Changes detected in DB. Syncing with Google Sheets...")
                    update_google_sheet(current_db_data)
                    last_data_hash = new_data_hash
                finally:
                    print("Lock released for DB to Sheets Sync.")
                    lock.release()  # Release the lock after completion
        # else:
        # print("No changes detected in DB.")

        # Small break between iterations to prevent aggressive CPU use
        time.sleep(3)


# ===================== Sheets to DB Sync ===================== #
def read_sheet_data():
    spreadsheet_id = read_spreadsheet_id()
    creds = google_sheets_auth()
    service = build("sheets", "v4", credentials=creds)

    range_name = "Sheet1!A1:Z1000"
    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    )
    values = result.get("values", [])
    if not values:
        print("No data found.")
        return []
    else:
        return values


def insert_into_mysql(data):
    connection = None
    total_inserted = 0
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        for row in data[1:]:
            if len(row) < 4 or not row[0].isdigit():
                continue

            while len(row) < 5:
                row.append(None)

            sql_insert_query = """
            INSERT INTO internships (id, company_name, job_title, cgpa_cutoff, remarks)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            company_name = VALUES(company_name),
            job_title = VALUES(job_title),
            cgpa_cutoff = VALUES(cgpa_cutoff),
            remarks = VALUES(remarks)
            """
            cursor.execute(sql_insert_query, row)
            total_inserted += 1

        connection.commit()
        print(
            f"{total_inserted} records inserted/updated successfully into the database."
        )

    except mysql.connector.Error as error:
        print(f"Failed to insert record into MySQL table {error}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def delete_from_mysql(ids_to_delete):
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        sql_delete_query = "DELETE FROM internships WHERE id = %s"
        cursor.executemany(sql_delete_query, [(id,) for id in ids_to_delete])

        connection.commit()
        print(f"{len(ids_to_delete)} records deleted from the database.")

    except mysql.connector.Error as error:
        print(f"Failed to delete records from MySQL table {error}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def detect_changes(old_data, new_data):
    """Compares old data with new data to detect rows that need to be inserted, updated, or deleted."""
    old_data_clean = clean_data(old_data)
    new_data_clean = clean_data(new_data)

    old_ids = {row[0] for row in old_data_clean[1:]}
    new_ids = {row[0] for row in new_data_clean[1:]}

    rows_to_insert_or_update = [
        row
        for row in new_data_clean[1:]
        if row[0] not in old_ids or row not in old_data_clean
    ]
    ids_to_delete = old_ids - new_ids

    return rows_to_insert_or_update, ids_to_delete


def clean_data(data):
    """Cleans the data by stripping all strings and removing empty rows. Ensures rows have the same number of columns."""
    if not data:
        return []

    max_columns = max(len(row) for row in data)
    cleaned_data = []
    for row in data:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        while len(cleaned_row) < max_columns:
            cleaned_row.append("")
        if any(cleaned_row):
            cleaned_data.append(cleaned_row)
    return cleaned_data


def sheets_to_db_sync():
    """Synchronize data from Google Sheets to MySQL."""
    last_data_hash = ""  # Initialize with an empty hash
    last_data = []  # Store the last data

    while not exit_flag:  # Exit if the flag is set to True
        new_data = read_sheet_data()
        new_data_hash = calculate_data_hash(new_data)

        if new_data_hash != last_data_hash:
            # Only acquire the lock if a change is detected
            if lock.acquire(blocking=False):
                try:
                    print("Lock acquired for Sheets to DB Sync.")
                    print("Data has changed in Sheets. Processing updates...")

                    rows_to_insert_or_update, ids_to_delete = detect_changes(
                        last_data, new_data
                    )

                    if rows_to_insert_or_update:
                        print("Inserting/Updating rows in DB...")
                        insert_into_mysql(
                            [
                                [
                                    "ID",
                                    "Company Name",
                                    "Job Title",
                                    "CGPA Cut-off",
                                    "Remarks",
                                ]
                            ]
                            + rows_to_insert_or_update
                        )

                    if ids_to_delete:
                        print("Deleting rows in DB...")
                        delete_from_mysql(ids_to_delete)

                    last_data = new_data
                    last_data_hash = new_data_hash
                finally:
                    print("Lock released for Sheets to DB Sync.")
                    lock.release()  # Release the lock after completion
        # else:
        # print("No changes detected in Sheets.")

        # Small break between iterations to prevent aggressive CPU use
        time.sleep(3)


# ===================== Main Code ===================== #
def keypress_exit_monitor():
    """Monitor for keypress 'e' to exit the program."""
    global exit_flag
    while not exit_flag:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key.lower() == b"e":  # Exit on 'e'
                print("Exit key pressed. Exiting...")
                exit_flag = True
                break


if __name__ == "__main__":
    # Start a thread to monitor keypress for exit
    keypress_thread = threading.Thread(target=keypress_exit_monitor)
    keypress_thread.start()

    # Run both syncs concurrently
    t1 = threading.Thread(target=db_to_sheets_sync)
    t2 = threading.Thread(target=sheets_to_db_sync)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    keypress_thread.join()  # Wait for the keypress thread to finish
