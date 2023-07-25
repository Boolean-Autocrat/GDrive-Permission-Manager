from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Flask, render_template, make_response, request
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
API_SERVICE_NAME = "drive"
API_VERSION = "v3"


def get_credentials():
    creds = None
    with open("token.json", "r") as token:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
    return creds


def list_shared_files_and_permissions():
    creds = get_credentials()
    shared_files = []
    return_list = []
    page_token = None
    try:
        service = build("drive", "v3", credentials=creds)
        results = (
            service.files()
            .list(
                q="trashed=false and 'me' in owners",
                fields="nextPageToken, files(id, name, permissions, webViewLink)",
                pageToken=page_token,
            )
            .execute()
        )
        shared_files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")

        if not shared_files:
            print("No files found.")
            return
        for file in shared_files:
            if len(file["permissions"]) != 1:
                buffer = [file["name"], file["webViewLink"]]
                for user in file["permissions"]:
                    if user["id"] == "anyoneWithLink":
                        buffer.append(["Anyone With Link"])
                    elif user["role"] == "owner":
                        pass
                    else:
                        buffer.append(
                            [user["displayName"], user["emailAddress"], user["role"]]
                        )
                return_list.append(buffer)
        return return_list
    except HttpError as error:
        print(f"An error occurred: {error}")


@app.route("/")
def index():
    shared_files = list_shared_files_and_permissions()
    return render_template("index.html", shared_files=shared_files)


if __name__ == "__main__":
    app.run(debug=True)
