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


def get_google_doc_url(doc: str | dict) -> str | None:
    """Generates URL to Google Doc when provided with doc_id (string) or doc (dict)."""
    doc_id = doc if isinstance(doc, str) else None

    if isinstance(doc, dict):
        document_id = doc.get("documentId", None)
        id = doc.get("id", None)
        doc_id = document_id if document_id else id

    if not doc_id:
        return None
    return f"https://docs.google.com/document/d/{doc_id}"


class ServerDocs:
    _cache: dict[str, str] = {}
    _template_id = None
    _credential_path = "credentials.json"
    _token_path = "./temp/google_token.json"
    _scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]

    @classmethod
    def available(cls):
        return os.path.exists(cls._credential_path)

    @classmethod
    def init(cls):
        if not cls.available():
            logging.warning(
                f"'{cls._credential_path}' not found. Follow these steps to generate a credentials file: https://developers.google.com/workspace/docs/api/quickstart/python"
            )
            return

        cls._template_id = os.getenv("GOOGLE_DOC_TEMPLATE_ID")
        if not cls._template_id:
            logging.warning(
                "No template-ID provided for Google Docs, bot will create docs with basic styling."
            )

        cls._get_creds()
        cls.sync_cache()
        logging.info("Google API initialised.")

    @classmethod
    def _get_creds(cls):
        """
        Get credentials for the Google API.
        Requires credentials json file, which you can obtain by following these steps: https://developers.google.com/workspace/docs/api/quickstart/python
        """

        creds = None
        if os.path.exists(cls._token_path):
            creds = Credentials.from_authorized_user_file(cls._token_path, cls._scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cls._credential_path, cls._scopes
                )
                creds = flow.run_local_server(port=0)
                with open(cls._token_path, "w") as token:
                    token.write(creds.to_json())

        return creds

    @classmethod
    def sync_cache(cls):
        """
        Checks the Google Drive for any documents with 'discord_guild_id' as property and caches them to memory.
        """
        logging.debug("Updating Google Doc cache")
        creds = cls._get_creds()
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

        cls._cache = guild_doc_map

    @classmethod
    def get(cls, itr: discord.Interactions) -> tuple[dict, str]:
        """Retrieves a Google Doc as a dictionary and a URL to the doc."""
        creds = cls._get_creds()
        guild_id = str(itr.guild_id)
        doc_id = cls._cache.get(guild_id, None)

        if doc_id is None:
            return None, None

        try:
            service = build("docs", "v1", credentials=creds)
            doc = service.documents().get(documentId=doc_id).execute()
            url = get_google_doc_url(doc)

            logging.info(f"Loaded google doc: {doc.get('title')}")
            return doc, url
        except HttpError as err:
            logging.error(err)
            return None, None

    @classmethod
    def create(cls, itr: discord.Interaction) -> tuple[dict, str]:
        """Generate a Google Doc from a template or blank, returns the new doc and a URL to the doc."""

        creds = cls._get_creds()
        guild_id = str(itr.guild_id)
        drive_service = build("drive", "v3", credentials=creds)

        try:
            new_file_metadata = {
                "name": f"{itr.guild.name} - Lore",
                "properties": {"discord_guild_id": guild_id},
            }

            if cls._template_id:
                new_doc = (
                    drive_service.files()
                    .copy(fileId=cls._template_id, body=new_file_metadata)
                    .execute()
                )

            else:
                new_file_metadata["mimeType"] = "application/vnd.google-apps.document"
                new_doc = drive_service.files().create(body=new_file_metadata).execute()

            doc_id = new_doc.get("id", None)
            drive_service.permissions().create(
                fileId=doc_id, body={"type": "anyone", "role": "writer"}
            ).execute()

            logging.info(f"Created Google Doc for server {itr.guild.name}")
            cls._cache[str(guild_id)] = doc_id
            return new_doc, get_google_doc_url(doc_id)

        except HttpError as error:
            logging.ERROR(f"Error whilst creating google doc for server:\n {error}")
            return None, None
