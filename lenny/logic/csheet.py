import io
import logging

import discord
from pypdf import PdfReader, PdfWriter

from logic.charactergen import CharacterGenResult

BLANK_PDF_PATH = "./assets/BlankCS.pdf"
reader = PdfReader(BLANK_PDF_PATH)


def generate_character_sheet(result: CharacterGenResult) -> discord.File:
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    fields = reader.get_fields()
    if fields is None:
        logging.error("CSheet.pdf does not have any valid fields.")

    data = {
        "Name": result.name,
        "Background": result.background.name,
        "Species": result.species.name,
        "Class": result.char_class.name,
        "Subclass": "",
        "Level": "1",
        "EXP": "",
        "AC": "",
        # "Shield": "",
        "HP": result.derived_stats.hp or 0,
        "HPMax": result.derived_stats.hp or 0,
        # "HPTemp": "",
        # "HDSpent": "",
        "HDMax": f"1d{result.char_class.hp or 0}",
    }

    for page in writer.pages:
        writer.update_page_form_field_values(page, data)  # type: ignore

    writer.set_need_appearances_writer()

    pdf_bytes = io.BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    filename = result.name.lower().replace(" ", "_")
    return discord.File(pdf_bytes, filename=f"{filename}.pdf")
