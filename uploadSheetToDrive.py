from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import os

# Updated scopes to include both Google Sheets and Drive permissions
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


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
    # Get the file name from the path
    file_name = os.path.basename(file_path).split(".")[0]

    # Check if the file already exists in Google Drive
    file_id = file_exists_in_drive(file_name)

    if file_id:
        # If the file exists, return the file ID without uploading again
        return file_id
    else:
        # Otherwise, upload the file to Google Drive
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

        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f'File uploaded successfully. File ID: {file.get("id")}')
        return file.get("id")


def save_spreadsheet_id(file_id):
    # Save the spreadsheet_id to a text file for future use
    with open("spreadsheet_id.txt", "w") as file:
        file.write(file_id)


# Example usage:
file_path = "Super.xlsx"  # Path to your uploaded Excel file

# Upload the Excel file to Google Sheets or use the existing file
spreadsheet_id = upload_excel_to_sheets(file_path)

# Save the spreadsheet ID in a text file for later use
save_spreadsheet_id(spreadsheet_id)
