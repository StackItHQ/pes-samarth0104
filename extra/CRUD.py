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


def write_to_sheet(values_to_insert):
    """Writes new data to the Google Sheet."""
    spreadsheet_id = read_spreadsheet_id()  # Get the stored spreadsheet ID
    creds = google_sheets_auth()  # Authenticate with Google Sheets
    service = build("sheets", "v4", credentials=creds)

    # Define the body with values to append to the sheet
    body = {"values": values_to_insert}

    # Call the Sheets API to append the new data
    range_name = "Sheet1!A1:Z1000"
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",  # Insert data as-is
            insertDataOption="INSERT_ROWS",  # Insert new rows
            body=body,
        )
        .execute()
    )

    print(f'{result.get("updates").get("updatedRows")} rows appended.')
    return result


def update_sheet_data(id_to_update, new_values):
    """Updates the row with the given ID in the Google Sheet."""
    data = read_sheet_data()

    # Find the row with the given ID
    for index, row in enumerate(data):
        if row[0] == id_to_update:
            # Update the row with new values
            range_name = f"Sheet1!A{index+1}:E{index+1}"  # Target row
            body = {"values": [new_values]}
            service = build("sheets", "v4", credentials=google_sheets_auth())
            service.spreadsheets().values().update(
                spreadsheetId=read_spreadsheet_id(),
                range=range_name,
                valueInputOption="RAW",
                body=body,
            ).execute()
            print(f"Row with ID {id_to_update} updated.")
            return
    print(f"No record found with ID {id_to_update}.")


def delete_sheet_data(id_to_delete):
    """Deletes the row with the given ID from the Google Sheet."""
    data = read_sheet_data()

    # Find the row with the given ID
    for index, row in enumerate(data):
        if len(row) > 0 and row[0] == id_to_delete:
            # Delete the row by replacing it with empty values
            range_name = f"Sheet1!A{index+1}:E{index+1}"  # Target row
            body = {"values": [[""] * len(row)]}
            service = build("sheets", "v4", credentials=google_sheets_auth())
            service.spreadsheets().values().update(
                spreadsheetId=read_spreadsheet_id(),
                range=range_name,
                valueInputOption="RAW",
                body=body,
            ).execute()
            print(f"Row with ID {id_to_delete} deleted.")
            return
    print(f"No record found with ID {id_to_delete}.")


def menu():
    """Displays the menu and processes user choices for CRUD operations."""
    print("\nGoogle Sheets CRUD Operations:")
    print("1. Create new entry")
    print("2. Read all data")
    print("3. Update an entry by ID")
    print("4. Delete an entry by ID")
    print("5. Exit")

    choice = input("Enter your choice (1-5): ")

    if choice == "1":
        print("\n-- Create New Entry --")
        new_entry = [
            input("ID: "),
            input("Company Name: "),
            input("Job Title: "),
            input("CGPA Cut-off: "),
            input("Remarks: "),
        ]
        write_to_sheet([new_entry])

    elif choice == "2":
        print("\n-- Read All Data --")
        read_sheet_data()

    elif choice == "3":
        print("\n-- Update Entry by ID --")
        id_to_update = input("Enter the ID to update: ")
        new_values = [
            id_to_update,
            input("New Company Name: "),
            input("New Job Title: "),
            input("New CGPA Cut-off: "),
            input("New Remarks: "),
        ]
        update_sheet_data(id_to_update, new_values)

    elif choice == "4":
        print("\n-- Delete Entry by ID --")
        id_to_delete = input("Enter the ID to delete: ")
        delete_sheet_data(id_to_delete)

    elif choice == "5":
        print("Exiting the program.")
        exit()
    else:
        print("Invalid choice. Please enter a valid option.")


if __name__ == "__main__":
    while True:
        menu()
