import mysql.connector
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
from googleapiclient.discovery import build
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def google_sheets_auth():
    """Handles Google Sheets API authentication and returns the credentials."""
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
    """Reads the spreadsheet ID from the text file."""
    if not os.path.exists("spreadsheet_id.txt"):
        raise FileNotFoundError("The spreadsheet ID file is missing.")
    with open("spreadsheet_id.txt", "r") as file:
        return file.read().strip()


def read_sheet_data():
    """Reads data from the Google Sheet."""
    spreadsheet_id = read_spreadsheet_id()  # Get the stored spreadsheet ID
    creds = google_sheets_auth()  # Authenticate with Google Sheets
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API to read data from the specific range in the sheet
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
        print("Data from the sheet:")
        for row in values:
            print(row)  # Print each row
        return values


def insert_into_mysql(data):
    """Inserts the Google Sheet data into a MySQL database."""
    connection = None  # Ensure the connection is initialized
    total_inserted = 0  # Track the number of records inserted
    try:
        # Establish a MySQL connection
        connection = mysql.connector.connect(
            host="localhost",
            database="superzz",  # Replace with your actual database name
            user="superjoin",  # The user you created
            password="super",  # The password for the user
        )

        cursor = connection.cursor()

        # Skip the header row and insert each row into the MySQL table
        for row in data[1:]:  # Skip the first row (headers)
            if (
                len(row) < 4 or not row[0].isdigit()
            ):  # Ensure at least 4 fields are present, and ID is numeric
                continue

            # Ensure that the row has 5 elements, filling in missing ones if necessary
            while len(row) < 5:
                row.append(
                    None
                )  # Fill missing values with NULL (for remarks or cgpa_cutoff)

            # Handle duplicate IDs with ON DUPLICATE KEY UPDATE
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
            total_inserted += 1  # Increment the count of inserted rows

        # Commit the transaction
        connection.commit()
        print(f"{total_inserted} records inserted successfully into the database.")

    except mysql.connector.Error as error:
        print(f"Failed to insert record into MySQL table {error}")

    finally:
        # Ensure the connection is closed if it was established
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


def upload_and_insert():
    """Uploads the sheet, reads data, and inserts it into MySQL."""
    # First, read the data from the Google Sheet
    data = read_sheet_data()

    # Insert the data into MySQL
    insert_into_mysql(data)


# Example usage:
if __name__ == "__main__":
    upload_and_insert()
