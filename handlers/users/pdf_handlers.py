"""Handlers for PDF generation and code handling."""
import os
from typing import Optional
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from utils.api_client import api_client
from utils.helpers import get_translation
from handlers.users.pdf import generate_pdf, generate_pdf_service

# Router not needed - functions are called from other handlers


async def handle_code(
    message: Message,
    state: FSMContext,
    customCode: Optional[str] = None,
    service: bool = False
):
    """Handle code input for PDF generation."""
    data = await state.get_data()
    lang = data.get("language", 'ru')
    selected_services_print = data.get("selected_services_print", [])
    
    selected_services_print = ",".join(selected_services_print)
    code = message.text if not customCode else customCode
    
    await message.answer(get_translation(lang, 'finding_results'))
    
    try:
        if service:
            data = await api_client.get_chosen_services(selected_services_print)
        else:
            data = await api_client.get_admittance_by_code(code)
        
        if not data or len(data) == 0:
            await message.answer(get_translation(lang, 'not_found'))
            return
        
        current_obj = data[0]
        patient_name = (
            f"{current_obj['patient']['first_name']} "
            f"{current_obj['patient']['last_name']}"
        )
        
        pdf_path = f"{patient_name}.pdf"
        
        if service:
            await generate_pdf_service(selected_services_print, pdf_path)
        else:
            guid = current_obj.get("guid")
            if guid:
                await generate_pdf(guid, pdf_path)
            else:
                await message.answer(get_translation(lang, 'not_found'))
                return
        
        try:
            await message.answer_document(document=FSInputFile(pdf_path))
            os.remove(pdf_path)
        except Exception as e:
            print(f"Error sending PDF: {e}")
            await message.answer(get_translation(lang, 'pdf_not_generated'))
            
    except Exception as e:
        print(f"Error in handle_code: {e}")
        await message.answer(get_translation(lang, 'try_again'))
