import logging
import os
import json
from typing import Literal
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
NamedStyle = Literal[
    "TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "NORMAL_TEXT"
]


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


class Paragraph:
    text: str
    start_index: int
    end_index: int
    style: NamedStyle

    def __init__(self, text: str, start_index: int, end_index: int, style: NamedStyle):
        self.text = text
        self.start_index = start_index
        self.end_index = end_index
        self.style = style

    def get_delete_request(self):
        return {
            "deleteContentRange": {
                "range": {"startIndex": self.start_index, "endIndex": self.end_index}
            }
        }

    def get_insert_request(self, new_text: str, index: int | None = None):
        self.text = new_text
        self.start_index = index if index else self.start_index
        self.end_index = self.start_index + len(self.text) + 1
        return {
            "insertText": {
                "location": {"index": self.start_index},
                "text": self.text + "\n",
            }
        }

    def get_style_request(self, style: NamedStyle | None):
        style = style or self.style
        return {
            "updateParagraphStyle": {
                "range": {"startIndex": self.start_index, "endIndex": self.end_index},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType",
            }
        }

    def get_replace_requests(
        self, new_text: str, style: NamedStyle | None = None
    ) -> list[dict]:
        return [
            self.get_delete_request(),
            self.get_insert_request(new_text),
            self.get_style_request(style),
        ]


class Entry:
    def __init__(self, title_para: Paragraph):
        self.title_para = title_para
        self.body_paragraphs: list[Paragraph] = []


class Section:
    def __init__(self, title_para: Paragraph):
        self.title_para = title_para
        self.entries: list[Entry] = []

    def get_entry_by_title(self, title: str) -> Entry | None:
        return next((e for e in self.entries if e.title_para.text == title), None)

    def get_entry_titles(self) -> list[str]:
        return [entry.title_para.text for entry in self.entries]


class Doc:
    _raw: dict
    title: str
    id: str
    url: str
    sections = list[Section]

    def __init__(self, raw: dict):
        self._raw = raw
        self.title = raw.get("title", "Untitled")
        self.id = raw.get("documentId", None)
        self.url = get_google_doc_url(self.id)
        self.sections: list[Section] = []
        self._parse()

    def _parse(self):
        current_section = None
        current_entry = None

        for el in self._raw.get("body", {}).get("content", []):
            para = el.get("paragraph")
            if not para or "elements" not in para:
                continue

            style = para.get("paragraphStyle", {}).get("namedStyleType", "NORMAL_TEXT")
            text = "".join(
                e.get("textRun", {}).get("content", "") for e in para["elements"]
            ).strip()
            if not text:
                continue

            start = el.get("startIndex")
            end = el.get("endIndex")
            if start is None or end is None:
                continue

            paragraph = Paragraph(text, start, end, style)

            if style == "HEADING_1":
                current_section = Section(paragraph)
                self.sections.append(current_section)
                current_entry = None

            elif style == "HEADING_2":
                current_entry = Entry(paragraph)
                if current_section:
                    current_section.entries.append(current_entry)

            elif style == "NORMAL_TEXT":
                if current_entry:
                    current_entry.body_paragraphs.append(paragraph)

    def get_section_by_title(self, title: str) -> Section | None:
        return next((e for e in self.sections if e.title_para.text == title), None)

    def get_section_titles(self) -> list[str]:
        return [section.title_para.text for section in self.sections]


class ServerDocs:
    """Class used to interact with Server's Google Docs"""

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
    def get(cls, itr: discord.Interaction) -> Doc | None:
        """Retrieves a Google Doc as a dictionary and a URL to the doc."""
        creds = cls._get_creds()
        guild_id = str(itr.guild_id)
        doc_id = cls._cache.get(guild_id, None)

        if doc_id is None:
            return None

        try:
            service = build("docs", "v1", credentials=creds)
            doc = service.documents().get(documentId=doc_id).execute()

            logging.info(f"Loaded google doc: {doc.get('title')}")
            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=4, sort_keys=True, ensure_ascii=False)
            return Doc(doc)
        except HttpError as err:
            logging.error(err)
            return None

    @classmethod
    def create(cls, itr: discord.Interaction) -> Doc | None:
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
            return Doc(new_doc)

        except HttpError as error:
            logging.ERROR(f"Error whilst creating google doc for server:\n {error}")
            return None


# class LoreDocEmbed(SimpleEmbed):
#     doc: Doc
#     view: LoreDocView
#     section: str | None = None
#     entry: str | None = None

#     def __init__(self, doc: Doc):
#         self.doc = doc
#         super().__init__(
#             title=doc.title,
#             description=None,
#             url=doc.url
#         )
