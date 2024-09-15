import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import hashlib
import threading
import time
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Global Mutex Lock and Exit Flag for Thread Synchronization
lock = threading.Lock()
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


def file_exists_in_drive(file_name):
    creds = google_sheets_auth()
    drive_service = build("drive", "v3", credentials=creds)

    # Search for the file by name
    query = f"name='{file_name}'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        print(f"File already exists in Drive. File ID: {files[0]['id']}")
        return files[0]["id"]
    else:
        return None


def upload_excel_to_sheets(file_path):
    """Uploads an Excel file to Google Sheets."""
    file_name = os.path.basename(file_path).split(".")[0]
    
    file_id = file_exists_in_drive(file_name)
    
    if file_id:
        return file_id
    else:
        creds = google_sheets_auth()
        drive_service = build("drive", "v3", credentials=creds)
    
        file_metadata = {
            "name": file_name,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
        media = MediaFileUpload(
            file_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f'File uploaded successfully. File ID: {file.get("id")}')
        return file.get("id")


def save_spreadsheet_id(file_id):
    """Save the spreadsheet ID in a text file for future use."""
    with open("spreadsheet_id_2.txt", "w") as file:
        file.write(file_id)


def read_sheet_data():
    """Reads data from Google Sheets, returning headers and data separately."""
    spreadsheet_id = read_spreadsheet_id()
    creds = google_sheets_auth()
    service = build("sheets", "v4", credentials=creds)

    range_name = "Sheet1!A1:Z1000"
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

    values = result.get("values", [])
    if not values:
        print("No data found.")
        return [], []
    else:
        headers = values[0]  # First row is the header
        data = values[1:]     # Remaining rows are the actual data
        return headers, data


def create_mysql_table(headers):
    """Dynamically create a MySQL table based on the Google Sheets headers."""
    table_name = "dynamic_table"  # You can generate a unique table name based on logic

    # Start building the CREATE TABLE SQL query
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
    
    # Define a basic data type for each column and make the first column the primary key
    column_definitions = []
    sanitized_headers = [header.replace(" ", "_").lower() for header in headers]
    
    column_definitions.append(f"{sanitized_headers[0]} VARCHAR(255) PRIMARY KEY")  # First column as primary key

    for header in sanitized_headers[1:]:
        column_definitions.append(f"{header} VARCHAR(255)")

    create_table_query += ", ".join(column_definitions)
    create_table_query += ");"

    # Execute the query
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
        print(f"Table `{table_name}` created or exists already.")
    except mysql.connector.Error as error:
        print(f"Failed to create table {error}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    return table_name


def insert_dynamic_data_into_mysql(table_name, headers, data):
    """Insert or update data from Google Sheets into the dynamically created MySQL table."""
    if not data:
        print("No data to insert.")
        return

    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        # Generate the INSERT INTO SQL query dynamically based on the headers
        sanitized_headers = [header.replace(" ", "_").lower() for header in headers]
        column_names = ", ".join(sanitized_headers)
        placeholders = ", ".join(["%s"] * len(headers))

        # Prepare the update part for ON DUPLICATE KEY
        update_clause = ", ".join([f"{col}=VALUES({col})" for col in sanitized_headers[1:]])

        insert_query = f"""
        INSERT INTO {table_name} ({column_names}) 
        VALUES ({placeholders}) 
        ON DUPLICATE KEY UPDATE {update_clause}
        """

        # Skip the first row as it contains headers, not actual data
        for row in data:
            if row == headers:  # Skip header row
                continue
            # If row is shorter than the number of headers, pad it with None (nulls)
            while len(row) < len(headers):
                row.append(None)
            cursor.execute(insert_query, row)

        connection.commit()
        print(f"Data inserted/updated in `{table_name}` successfully.")

    except mysql.connector.Error as error:
        print(f"Failed to insert/update data into MySQL table {error}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



def read_spreadsheet_id():
    if not os.path.exists("spreadsheet_id_2.txt"):
        raise FileNotFoundError("The spreadsheet ID file is missing.")
    with open("spreadsheet_id_2.txt", "r") as file:
        return file.read().strip()


# Sync functionality

def fetch_from_mysql(table_name):
    """Fetch all data from the MySQL table."""
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()

        return records

    except mysql.connector.Error as error:
        print(f"Failed to read data from MySQL table {error}")
        return []

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def calculate_data_hash(data):
    """Calculate a hash for the MySQL/Google Sheets data to detect changes efficiently."""
    hash_md5 = hashlib.md5()
    for row in data:
        row_string = "".join(map(str, row))  # Convert each row to a string
        hash_md5.update(row_string.encode("utf-8"))
    return hash_md5.hexdigest()


def db_to_sheets_sync():
    """Synchronize data from MySQL to Google Sheets."""
    table_name = "dynamic_table"  # Same table created dynamically
    last_data_hash = ""  # Initialize with an empty hash

    while not exit_flag:
        current_db_data = fetch_from_mysql(table_name)
        new_data_hash = calculate_data_hash(current_db_data)

        if new_data_hash != last_data_hash:
            # Only acquire the lock if a change is detected
            if lock.acquire(blocking=False):
                try:
                    print("Lock acquired for DB to Sheets Sync.")
                    print("Changes detected in DB. Syncing with Google Sheets...")
                    headers, _ = read_sheet_data()
                    update_google_sheet(current_db_data, headers)
                    last_data_hash = new_data_hash
                finally:
                    print("Lock released for DB to Sheets Sync.")
                    lock.release()  # Release the lock after completion

        time.sleep(3)


def update_google_sheet(data, headers):
    """Update Google Sheet with the data fetched from MySQL."""
    creds = google_sheets_auth()
    service = build("sheets", "v4", credentials=creds)

    spreadsheet_id = read_spreadsheet_id()
    sheet = service.spreadsheets()

    clear_range = "Sheet1!A2:Z1000"
    sheet.values().clear(spreadsheetId=spreadsheet_id, range=clear_range).execute()

    values = [headers]  # First row is the headers
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


# Sheets to DB Sync
def sheets_to_db_sync():
    """Synchronize data from Google Sheets to MySQL."""
    table_name = "dynamic_table"  # Same table created dynamically
    last_data_hash = ""  # Initialize with an empty hash

    while not exit_flag:
        # Read the Google Sheets data
        headers, current_sheet_data = read_sheet_data()
        new_data_hash = calculate_data_hash(current_sheet_data)

        if new_data_hash != last_data_hash:
            # Only acquire the lock if a change is detected
            if lock.acquire(blocking=False):
                try:
                    print("Lock acquired for Sheets to DB Sync.")
                    print("Changes detected in Sheets. Syncing with MySQL...")
                    insert_dynamic_data_into_mysql(table_name, headers, current_sheet_data)
                    last_data_hash = new_data_hash
                finally:
                    print("Lock released for Sheets to DB Sync.")
                    lock.release()  # Release the lock after completion

        time.sleep(3)


# Main code for two-way synchronization
if __name__ == "__main__":
    # Step 1: Upload the Excel file to Google Sheets
    file_path = "testing.xlsx"  # Path to your uploaded Excel file
    spreadsheet_id = upload_excel_to_sheets(file_path)
    save_spreadsheet_id(spreadsheet_id)

    # Step 2: Read data from Google Sheets
    headers, data = read_sheet_data()

    if headers and data:
        # Step 3: Dynamically create a MySQL table based on the sheet headers
        table_name = create_mysql_table(headers)

        # Step 4: Insert or update data from Google Sheets into the dynamically created MySQL table
        insert_dynamic_data_into_mysql(table_name, headers, data)

    # Step 5: Start syncing MySQL to Google Sheets and Sheets to MySQL
    t1 = threading.Thread(target=sheets_to_db_sync)
    t2 = threading.Thread(target=db_to_sheets_sync)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
