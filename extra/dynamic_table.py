import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import hashlib
import time
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

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
    
    # Define a basic data type for each column
    column_definitions = []
    for header in headers:
        sanitized_header = header.replace(" ", "_").lower()  # Sanitize header names for SQL
        column_definitions.append(f"{sanitized_header} VARCHAR(255)")

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
    """Insert data from Google Sheets into the dynamically created MySQL table."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost", database="superzz", user="superjoin", password="super"
        )
        cursor = connection.cursor()

        # Generate the INSERT INTO SQL query dynamically based on the headers
        column_names = ", ".join([header.replace(" ", "_").lower() for header in headers])
        placeholders = ", ".join(["%s"] * len(headers))
        insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

        for row in data:
            # If row is shorter than the number of headers, pad it with None (nulls)
            while len(row) < len(headers):
                row.append(None)
            cursor.execute(insert_query, row)

        connection.commit()
        print(f"Data inserted into `{table_name}` successfully.")

    except mysql.connector.Error as error:
        print(f"Failed to insert data into MySQL table {error}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# Helper function to read spreadsheet ID from file
def read_spreadsheet_id():
    if not os.path.exists("spreadsheet_id_2.txt"):
        raise FileNotFoundError("The spreadsheet ID file is missing.")
    with open("spreadsheet_id_2.txt", "r") as file:
        return file.read().strip()


# ===================== Main Code ===================== #
if __name__ == "__main__":
    # Step 1: Upload the Excel file to Google Sheets
    file_path = "testing.xlsx"  # Path to your uploaded Excel file
    spreadsheet_id = upload_excel_to_sheets(file_path)

    # Save the spreadsheet ID in a text file for future use
    save_spreadsheet_id(spreadsheet_id)

    # Step 2: Read data from the Google Sheet
    headers, data = read_sheet_data()

    if headers and data:
        # Step 3: Dynamically create a MySQL table based on the sheet headers
        table_name = create_mysql_table(headers)

        # Step 4: Insert data from Google Sheets into the dynamically created MySQL table
        insert_dynamic_data_into_mysql(table_name, headers, data)
