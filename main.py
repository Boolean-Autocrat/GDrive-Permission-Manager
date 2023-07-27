from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Flask, render_template, make_response, request, redirect
import os
import webview

app = Flask(__name__, static_folder="./static", template_folder="./templates")
app.secret_key = os.urandom(24)

SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive",
]
API_SERVICE_NAME = "drive"
API_VERSION = "v3"


def resource_path(relative):
    return os.path.join(os.environ.get("_MEIPASS2", os.path.abspath(".")), relative)


def get_credentials():
    credential = None
    if not credential:
        flow = InstalledAppFlow.from_client_secrets_file(
            resource_path("credentials.json"), SCOPES
        )
        credential = flow.run_local_server(port=0)
    return credential


def list_shared_files_and_permissions(creds):
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
    global creds
    creds = get_credentials()
    shared_files = list_shared_files_and_permissions(creds)
    return render_template("index.html", shared_files=shared_files)


@app.route("/revoke_user_permissions", methods=["POST"])
def revoke_user_permissions():
    email = request.form["email"]
    try:
        service = build("drive", "v3", credentials=creds)

        # Retrieve the list of all shared files
        shared_files = []
        page_token = None

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
        for file in shared_files:
            if len(file["permissions"]) != 1:
                for user in file["permissions"]:
                    if user["id"] == "anyoneWithLink":
                        continue
                    elif user["emailAddress"] == email:
                        file_id = file["id"]
                        print(file_id)
                        permission_id = user["id"]
                        print(permission_id)
                        service.permissions().delete(
                            fileId=file_id, permissionId=permission_id
                        ).execute()

        # Redirect back to the index page after revoking permissions
        return (
            "Successfully deleted user permissions for "
            + email
            + ". You may now close this window."
        )
    except HttpError as error:
        print(f"An error occurred: {error}")


webview.create_window(
    "Drive Permission Manager",
    app,
    text_select=True,
)

if __name__ == "__main__":
    # app.run()
    webview.start()
