import logging
import os

import discord
import googleapiclient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

googleapiclient.discovery._DEFAULT_DISCOVERY_DOC_CACHE = (
    False  # Suppress file_cache warning
)
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]  # https://developers.google.com/workspace/docs/api/auth
TOKEN_PATH = "./temp/google_token.json"
TEMPLATE_ID = None
SERVER_DOCS: dict[str, str] = {}


def google_available():
    return os.path.exists("credentials.json")


def init_google_docs():
    global TEMPLATE_ID
    if not google_available():
        logging.warning(
            "'credentials.json' not found in root folder. Follow these steps to generate a credentials.json file: https://developers.google.com/workspace/docs/api/quickstart/python"
        )
        return

    TEMPLATE_ID = os.getenv("GOOGLE_DOC_TEMPLATE_ID")
    if not TEMPLATE_ID:
        logging.warning(
            "No template-ID provided for Google Docs, bot will create docs with basic styling."
        )

    _get_creds()
    _update_server_docs()
    logging.info("Google API initialised.")


def _get_creds():
    """
    Get credentials for the Google API.
    Requires credentials.json to be located in the root folder.
    https://developers.google.com/workspace/docs/api/quickstart/python
    """

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

    return creds


def _update_server_docs() -> dict:
    """
    Checks the Google Drive for any documents with 'discord_guild_id' as property and caches them to memory.
    """
    global SERVER_DOCS
    logging.debug("Updating Google Doc cache")
    creds = _get_creds()
    service = build("drive", "v3", credentials=creds)

    page_token = None
    guild_doc_map = {}
    while True:
        results = (
            service.files()
            .list(
                q="mimeType='application/vnd.google-apps.document'",  # Only get google docs
                pageSize=100,
                fields="nextPageToken, files(id, name, properties)",
                pageToken=page_token,
            )
            .execute()
        )

        for file in results.get("files", []):
            props = file.get("properties", {})
            guild_id = props.get("discord_guild_id")
            if guild_id:
                guild_doc_map[str(guild_id)] = file["id"]

        page_token = results.get("nextPageToken", None)
        if not page_token:
            break

    SERVER_DOCS = guild_doc_map


def _server_has_doc(guild_id: str | None):
    """
    Evaluates if a server has a Google Doc.
    """
    if not guild_id:
        return False

    doc_id = SERVER_DOCS.get(str(guild_id), None)
    return doc_id is not None


def create_doc_for_server(itr: discord.Interaction):
    creds = _get_creds()
    guild_id = str(itr.guild_id)
    drive_service = build("drive", "v3", credentials=creds)

    if _server_has_doc(guild_id):
        logging.debug(f"Server {guild_id} already has a Google Doc!")
        return None

    try:
        new_file_metadata = {
            "name": f"{itr.guild.name} - Lore",
            "properties": {"discord_guild_id": guild_id},
        }

        if TEMPLATE_ID:
            new_doc = (
                drive_service.files()
                .copy(fileId=TEMPLATE_ID, body=new_file_metadata)
                .execute()
            )
            doc_id = new_doc["id"]
            logging.info(f"Created Google Doc for server {guild_id}: {doc_id}")

        else:
            new_file_metadata["mimeType"] = "application/vnd.google-apps.document"
            blank_doc = drive_service.files().create(body=new_file_metadata).execute()
            doc_id = blank_doc["id"]
            logging.info(f"Created blank Google Doc for server {guild_id}: {doc_id}")

        # Make editable by anyone with link
        drive_service.permissions().create(
            fileId=doc_id, body={"type": "anyone", "role": "writer"}
        ).execute()

        SERVER_DOCS[str(guild_id)] = doc_id  # Add to cache
        return f"https://docs.google.com/document/d/{doc_id}"
    except HttpError as error:
        logging.ERROR(f"Error whilst creating server google doc: {error}")
        return None


def get_server_doc(itr: discord.Interaction):
    creds = _get_creds()
    guild_id = str(itr.guild_id)
    doc_id = SERVER_DOCS.get(guild_id, None)

    if doc_id is None:
        return None

    try:
        service = build("docs", "v1", credentials=creds)
        doc = service.documents().get(documentId=doc_id).execute()
        logging.info(f"Loaded google doc: {doc.get('title')}")
        return doc
    except HttpError as err:
        logging.error(err)
        return None
