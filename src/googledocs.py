import datetime
import logging
import os
from typing import Literal
import discord
from discord import Interaction
import discord.ui as ui
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from embeds import SimpleEmbed, log_button_press
from modals import SimpleModal

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

    def get_delete_request(self, for_replace: bool = False) -> dict:
        """Use `for_replace = True` when deleting a paragraph that will be replaced by new text. (Handles newline at end differently)"""
        self.text = (
            self.text.rstrip()
        )  # google automatically adds newline at end, needs to be trimmed to avoid double newlines.

        if not for_replace:
            self.end_index -= (
                1  # When deleting full text, we need to ignore the newline at the end.
            )

        return {
            "deleteContentRange": {
                "range": {"startIndex": self.start_index, "endIndex": self.end_index}
            }
        }

    def get_insert_request(self, new_text: str, index: int | None = None) -> dict:
        self.text = new_text
        self.start_index = index if index else self.start_index
        self.end_index = self.start_index + len(self.text) + 1
        return {
            "insertText": {
                "location": {"index": self.start_index},
                "text": self.text + "\n",
            }
        }

    def get_style_request(self, style: NamedStyle | None) -> dict:
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
            self.get_delete_request(for_replace=True),
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
    guild_id: str
    url: str
    sections = list[Section]
    created_at: datetime.datetime

    def __init__(self, raw: dict, guild_id: str):
        self._raw = raw
        self.title = raw.get("title", "Untitled")
        self.id = raw.get("documentId", None)
        self.guild_id = guild_id
        self.url = get_google_doc_url(self.id)
        self.sections: list[Section] = []
        self.created_at = datetime.datetime.now()
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

    _cache: dict[str, Doc | str] = {}
    _template_id: str = None
    _credential_path: str = "credentials.json"
    _token_path: str = "./temp/google_token.json"
    _scopes: list[str] = [
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
    def _drive_service(cls):
        creds = cls._get_creds()
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    @classmethod
    def _docs_service(cls):
        creds = cls._get_creds()
        return build("docs", "v1", credentials=creds, cache_discovery=False)

    @classmethod
    def sync_cache(cls):
        """
        Checks the Google Drive for any documents with 'discord_guild_id' as property and caches them to memory.
        """
        logging.debug("Updating Google Doc cache")

        page_token = None
        guild_doc_map = {}
        while True:
            results = (
                cls._drive_service()
                .files()
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
                    guild_doc_map[str(guild_id)] = file[
                        "id"
                    ]  # Cache the ID only, we only load docs on demand

            page_token = results.get("nextPageToken", None)
            if not page_token:
                break

        cls._cache = guild_doc_map

    @classmethod
    def uncache_doc(cls, doc: Doc):
        """
        Removes a document from the cache.
        This is useful when you want to force a reload of the document from Google Drive.
        """
        if not isinstance(doc, Doc):
            return

        logging.debug(f"Uncaching Google Doc for server {doc.guild_id}")
        guild_id = str(doc.guild_id)
        cls._cache[guild_id] = doc.id

    @classmethod
    def get(
        cls, itr: discord.Interaction, allow_refresh_from_drive: bool = True
    ) -> Doc | None:
        """Retrieves a Google Doc as a dictionary and a URL to the doc."""
        guild_id = str(itr.guild_id)

        doc = cls._cache.get(guild_id, None)
        if doc is None:
            return None

        if isinstance(doc, Doc):
            now = datetime.datetime.now()
            if now - doc.created_at < datetime.timedelta(minutes=15):
                logging.debug(
                    f"Loading Google Doc for server {itr.guild.name} from google cache"
                )
                return doc

            if not allow_refresh_from_drive:
                return doc

        logging.debug(
            f"Loading Google Doc for server {itr.guild.name} from google drive"
        )
        doc_id = doc.id if isinstance(doc, Doc) else doc
        try:
            new_doc = cls._docs_service().documents().get(documentId=doc_id).execute()
            doc = Doc(new_doc, guild_id)
            cls._cache[str(guild_id)] = doc
            return doc
        except HttpError as err:
            logging.error(err)

            return doc  # Return cached

    @classmethod
    def create(cls, itr: discord.Interaction) -> Doc | None:
        """Generate a Google Doc from a template or blank, returns the new doc and a URL to the doc."""
        guild_id = str(itr.guild_id)
        service = cls._drive_service()

        try:
            new_file_metadata = {
                "name": f"{itr.guild.name} - Lore",
                "properties": {"discord_guild_id": guild_id},
            }

            if cls._template_id:
                new_doc = (
                    service.files()
                    .copy(fileId=cls._template_id, body=new_file_metadata)
                    .execute()
                )

            else:
                new_file_metadata["mimeType"] = "application/vnd.google-apps.document"
                new_doc = service.files().create(body=new_file_metadata).execute()

            doc_id = new_doc.get("id", None)
            service.permissions().create(
                fileId=doc_id, body={"type": "anyone", "role": "writer"}
            ).execute()

            logging.info(f"Created Google Doc for server {itr.guild.name}")
            cls._cache[str(guild_id)] = doc_id
            return Doc(new_doc, guild_id)

        except HttpError as e:
            logging.error(f"Error whilst creating google doc for server:\n {e}")
            return None

    @classmethod
    def apply_requests(cls, doc: Doc, requests: list[dict]) -> bool:
        """
        Applies a batchUpdate to a Google Doc with the given list of requests.

        Args:
            doc_id (str): The ID of the Google Document.
            requests (list[dict]): A list of Google Docs API requests to apply.

        Returns:
            bool: True if update succeeded, False otherwise.
        """
        try:
            cls._docs_service().documents().batchUpdate(
                documentId=doc.id, body={"requests": requests}
            ).execute()
            logging.info(f"Applied {len(requests)} requests to Google Doc {doc.title}")
            cls._cache[doc.guild_id] = doc.id  # Enforce cache update on next load
            return True

        except HttpError as error:
            logging.error(
                f"Error applying requests to Google Doc {doc.title}:\n{error}"
            )
            return False


###############
# EMBED CLASSES
###############


class LoreEditModal(SimpleModal):
    def __init__(
        self, itr: Interaction, doc: Doc, section: Section, entry: Entry | None = None
    ):
        modal_title = "Edit Entry" if entry else "Edit Section"
        super().__init__(itr, modal_title)

        self.doc = doc
        self.section = section
        self.entry = entry
        title_paragraph = entry.title_para if entry else section.title_para
        title_placeholder = title_paragraph.text.strip() or "Untitled"
        if len(title_placeholder) > 100:  # Placeholder max length is 100
            title_placeholder = title_placeholder[:97] + "..."

        self.add_item(
            ui.TextInput(
                label="Title",
                placeholder=title_placeholder,
                default=title_placeholder,
                style=discord.TextStyle.short,
                required=True,
            )
        )

        if not entry:
            return

        for para in entry.body_paragraphs:
            para_placeholder = para.text.strip() or "Lorem Ipsum, dolor sit amet..."
            if len(para_placeholder) > 100:  # Placeholder max length is 100
                para_placeholder = para_placeholder[:97] + "..."

            self.add_item(
                ui.TextInput(
                    label="Content",
                    placeholder=para_placeholder,
                    default=para.text or None,
                    style=discord.TextStyle.long,
                    required=False,
                )
            )

    async def on_submit(self, itr: Interaction):
        requests = []
        title_paragraph = (
            self.entry.title_para if self.entry else self.section.title_para
        )

        new_title = self.children[0].value.strip()
        if not new_title:
            await itr.response.send_message("Title cannot be empty.", ephemeral=True)
            return
        requests.extend(title_paragraph.get_replace_requests(new_title))

        if self.entry:
            content_inputs = self.children[1:]  # Skip title
            for i, content_input in enumerate(content_inputs):
                new_text = content_input.value
                if i > len(self.entry.body_paragraphs):
                    break

                para = self.entry.body_paragraphs[i]
                if new_text == para.text:
                    continue  # Unchanged, skip

                # Insert new requests at the start, so doc is edited from last to first
                if not new_text:
                    requests = [para.get_delete_request()] + requests
                else:
                    requests = para.get_replace_requests(new_text) + requests

        if not requests:
            await itr.response.send_message("No changes made.", ephemeral=True)
            return

        ServerDocs.apply_requests(self.doc, requests)
        doc = ServerDocs.get(itr)

        if self.entry:
            embed = LoreDocEmbed(
                doc, section=self.section.title_para.text, entry=new_title
            )
        else:
            embed = LoreDocEmbed(doc, section=new_title)

        await itr.response.edit_message(embed=embed, view=embed.view)


class LoreDocView(ui.View):
    def __init__(self, doc: Doc):
        super().__init__()
        self.doc = doc

        # Section Dropdown Select
        # Add Section Button
        # TODO: Nav Buttons (Pagination)
        # TODO: Doc or Tab Select (Multi-doc support)

    @ui.button(
        label="Add Section", style=discord.ButtonStyle.success, custom_id="add_btn"
    )
    async def add(self, itr: Interaction, btn: ui.Button):
        """Button to add a new section to the document."""
        await itr.response.send_message("Sorry, not implemented yet.", ephemeral=True)
        # await itr.response.send_modal(modal=SimpleModal(itr, "Add New Section"))


class LoreSectionView(ui.View):
    def __init__(self, doc: Doc, section: Section):
        super().__init__()
        self.doc = doc
        self.section = section

        # Entry Dropdown Select
        # TODO: Nav Buttons (Pagination)

    @ui.button(
        label="Add Entry", style=discord.ButtonStyle.success, custom_id="add_btn"
    )
    async def add(self, itr: Interaction, btn: ui.Button):
        """Button to add a new entry to the document."""
        await itr.response.send_message("Sorry, not implemented yet.", ephemeral=True)
        # await itr.response.send_modal(modal=SimpleModal(itr, "Add New Entry"))

    @ui.button(label="Edit", style=discord.ButtonStyle.success, custom_id="edit_btn")
    async def edit(self, itr: Interaction, btn: ui.Button):
        """Button to add a new entry to the document."""
        await itr.response.send_modal(LoreEditModal(itr, self.doc, self.section))

    @ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete_btn")
    async def delete(self, itr: Interaction, btn: ui.Button):
        """Button to delete the section."""
        log_button_press(itr, btn, "LoreSectionView.delete")
        # TODO CONFIRM MODAL

        # TODO move request logic to SECTION class
        # if not self.section.entries:
        #     ServerDocs.apply_requests(
        #         self.doc, [self.section.title_para.get_delete_request()]
        #     )

        # else:
        #     requests = []
        #     for para in self.section.entries:
        #         requests.append(para.get_delete_request())
        #     requests.append(self.entry.title_para.get_delete_request())
        #     ServerDocs.apply_requests(self.doc, requests)

        await self._go_back(itr)

    @ui.button(label="Back", style=discord.ButtonStyle.primary, custom_id="back_btn")
    async def back(self, itr: Interaction, btn: ui.Button):
        """Button to go back to doc overview."""
        log_button_press(itr, btn, "LoreSectionView.back")
        await self._go_back(itr)

    async def _go_back(self, itr: Interaction):
        """Helper method to navigate back, call this from delete after deletion."""
        doc = ServerDocs.get(itr)
        embed = LoreDocEmbed(doc)
        await itr.response.edit_message(embed=embed, view=embed.view)

class LoreEntryView(ui.View):
    def __init__(self, doc: Doc, section: Section, entry: Entry):
        super().__init__()
        self.doc = doc
        self.section = section
        self.entry = entry

    @ui.button(label="Edit", style=discord.ButtonStyle.success, custom_id="add_btn")
    async def edit(self, itr: Interaction, btn: ui.Button):
        """Button to add a new entry to the document."""
        await itr.response.send_modal(
            LoreEditModal(itr, self.doc, self.section, self.entry)
        )

    @ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete_btn")
    async def delete(self, itr: Interaction, btn: ui.Button):
        """Button to delete the section."""
        log_button_press(itr, btn, "LoreEntryView.delete")
        # TODO CONFIRM MODAL

        # TODO move request logic to entry class
        if not self.entry.body_paragraphs:
            ServerDocs.apply_requests(
                self.doc, [self.entry.title_para.get_delete_request()]
            )

        else:
            requests = []
            for para in self.entry.body_paragraphs:
                requests.append(para.get_delete_request())
            requests.append(self.entry.title_para.get_delete_request())
            ServerDocs.apply_requests(self.doc, requests)

        await self._go_back(itr)

    @ui.button(label="Back", style=discord.ButtonStyle.primary, custom_id="back_btn")
    async def back(self, itr: Interaction, btn: ui.Button):
        """Button to go back to section overview."""
        log_button_press(itr, btn, "LoreEntryView.back")
        await self._go_back(itr)

    async def _go_back(self, itr: Interaction):
        """Helper method to navigate back, call this from delete after deletion."""
        doc = ServerDocs.get(itr)
        embed = LoreDocEmbed(doc, section=self.section.title_para.text)
        await itr.response.edit_message(embed=embed, view=embed.view)


class LoreDocEmbed(SimpleEmbed):
    doc: Doc
    view: ui.View  # TODO
    section: str | None = None
    entry: str | None = None

    def __init__(self, doc: Doc, section: str | None = None, entry: str | None = None):
        self.doc = doc

        if section and section not in doc.get_section_titles():
            ServerDocs.uncache_doc(doc)
        self.section = doc.get_section_by_title(section) if section else None

        if entry and self.section and entry not in self.section.get_entry_titles():
            ServerDocs.uncache_doc(doc)
        self.entry = (
            self.section.get_entry_by_title(entry) if entry and self.section else None
        )

        if self.section and not self.entry:  # Section Info
            title = self.section.title_para.text.strip()
            entries = self.section.get_entry_titles()
            description = (
                "**Entries:**\n - " + "\n - ".join(entries)
                if entries
                else "*No entries found in this section.*"
            )

            self.view = LoreSectionView(doc, self.section)

        elif self.section and self.entry:  # Entry Info
            title = f"{self.entry.title_para.text.strip()} ({self.section.title_para.text.strip()})"
            paragraphs = self.entry.body_paragraphs
            description = (
                "\n".join(paragraph.text.strip() for paragraph in paragraphs)
                if paragraphs
                else "*No content found in this entry.*"
            )
            self.view = LoreEntryView(doc, self.section, self.entry)

        else:  # Doc Info
            title = doc.title
            sections = doc.get_section_titles()
            description = (
                "**Sections:**\n - " + "\n - ".join(sections)
                if sections
                else "*No sections found in this document.*"
            )
            self.view = LoreDocView(doc)

        super().__init__(title=title, description=description, url=doc.url)
