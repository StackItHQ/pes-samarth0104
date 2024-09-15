import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import time

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

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

def read_sheet_data():
    spreadsheet_id = read_spreadsheet_id()
    creds = google_sheets_auth()
    service = build("sheets", "v4", credentials=creds)

    range_name = "Sheet1!A1:Z1000"
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
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
            host="localhost",
            database="superzz",
            user="superjoin",
            password="super"
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
        print(f"{total_inserted} records inserted/updated successfully into the database.")

    except mysql.connector.Error as error:
        print(f"Failed to insert record into MySQL table {error}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def delete_from_mysql(ids_to_delete):
    """Delete rows from the MySQL database based on missing IDs."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="superzz",
            user="superjoin",
            password="super"
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

def clean_data(data):
    """Cleans the data by stripping all strings and removing empty rows. Ensures rows have the same number of columns."""
    if not data:
        return []
    
    max_columns = max(len(row) for row in data)
    cleaned_data = []
    for row in data:
        cleaned_row = [str(cell).strip() if cell is not None else '' for cell in row]
        while len(cleaned_row) < max_columns:
            cleaned_row.append('')  # Add empty strings for missing columns
        if any(cleaned_row):  # Ignore completely empty rows
            cleaned_data.append(cleaned_row)
    return cleaned_data

def detect_changes(old_data, new_data):
    """Compares old data with new data to detect rows that need to be inserted, updated, or deleted."""
    old_data_clean = clean_data(old_data)
    new_data_clean = clean_data(new_data)

    old_ids = {row[0] for row in old_data_clean[1:]}  # Skip headers
    new_ids = {row[0] for row in new_data_clean[1:]}

    # Rows to insert or update
    rows_to_insert_or_update = [row for row in new_data_clean[1:] if row[0] not in old_ids or row not in old_data_clean]

    # Rows to delete
    ids_to_delete = old_ids - new_ids  # IDs that existed before but are not in the new data

    return rows_to_insert_or_update, ids_to_delete

def poll_and_update():
    last_data = []  # Initialize with empty data

    while True:
        new_data = read_sheet_data()

        rows_to_insert_or_update, ids_to_delete = detect_changes(last_data, new_data)

        if rows_to_insert_or_update:
            print("Inserting/Updating rows...")
            insert_into_mysql([['ID', 'Company Name', 'Job Title', 'CGPA \nCut-off', 'Remarks']] + rows_to_insert_or_update)

        if ids_to_delete:
            print("Deleting rows...")
            delete_from_mysql(ids_to_delete)

        last_data = new_data  # Update the last_data with new_data after changes

        time.sleep(30)  # Poll every 10 seconds (adjust as needed)

if __name__ == "__main__":
    poll_and_update()
