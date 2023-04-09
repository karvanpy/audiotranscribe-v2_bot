import logging
import os
import speech_recognition as sr
from credentials import BOT_API
from transcribe import transcribe
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (CommandHandler,
                          filters, MessageHandler,
                          ContextTypes, ApplicationBuilder, CallbackQueryHandler)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

total_usages = 0


# Greet the user and ask which language they want to transcribe
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data['total_usages'] = total_usages
    logger.info("User %s started the conversation.", user.first_name)
    await update.message.reply_text(
        f"Hi {user.first_name}! \n"
        f"I can transcribe audio for you. Which language do you want me to transcribe to?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🇮🇩 INDONESIA", callback_data='id-ID'),
            InlineKeyboardButton("🇺🇸 ENGLISH", callback_data='en-US')
        ]])
    )


# Save the language selection and ask the user to send an audio file or record a sound
async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['language'] = lang
    logger.info("Language %s selected.", lang)

    await query.edit_message_text(text=f"*{lang}* language selected.\n"
                                       f"Please send an audio file or record a sound.",
                                  parse_mode='MARKDOWN')


async def transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    file_obj = update.message.voice

    file_id = file_obj.file_id
    file_name = "audio_temp"
    mime_type = file_obj.mime_type.split('/')[-1]
    full_file_name = f"{file_name}.{mime_type}"

    logger.info("User %s sent %s. ", user.first_name, full_file_name)

    file_obj_info = {
        "chat_id": update.message.chat_id,
        "message_id": update.message.message_id,
    }

    # Get the file and save it locally
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(full_file_name)

    lang = context.user_data['language']

    # Give bot typing to let user know that the process is starting
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    # Let user know transcription is under processing
    message = await context.bot.send_message(chat_id=update.message.chat_id, text="Processing...")

    # Transcribe the audio file
    result = transcribe(full_file_name, language=lang)

    # Increment total usages
    context.user_data['total_usages'] += 1
    # tot = context.user_data['total_usages']

    logger.info("chat_id: %s, message_id: %s", message.chat_id, message.message_id)
    try:
        await context.bot.edit_message_text(chat_id=message.chat_id, message_id=message.message_id,
                                            text=f"*Transcription*:\n", parse_mode='MARKDOWN')
        await update.message.reply_text(result[0])
        await context.bot.delete_message(chat_id=file_obj_info.get("chat_id"),
                                         message_id=file_obj_info.get("message_id"))
    except sr.UnknownValueError:
        await update.message.reply_text('Sorry, I could not understand what you said.')
    except sr.RequestError as e:
        await update.message.reply_text(
            'Sorry, I could not request results from Google Speech Recognition service; {0}'.format(e))
    os.remove(full_file_name)  # original file is deleted
    os.remove(result[-1])  # transcription file is deleted
    logger.info("Remove [%s]", full_file_name)


async def transcribe_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    file_obj = update.message.document
    logger.info("User %s sent %s. ", user.first_name, file_obj.file_name)

    file_obj_info = {
        "chat_id": update.message.chat_id,
        "message_id": update.message.message_id,
    }

    file_id = file_obj.file_id
    file_name = file_obj.file_name

    # Get the file and save it locally
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(file_name)

    lang = context.user_data['language']

    # Give bot typing to let user know that the process is starting
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    # Let user know transcription is under processing
    message = await context.bot.send_message(chat_id=update.message.chat_id, text="Processing...")

    # Transcribe the file
    result = transcribe(file_name, language=lang)

    # Increase total usages
    context.user_data['total_usages'] += 1
    # tot = context.user_data['total_usages']

    logger.info("chat_id: %s, message_id: %s", message.chat_id, message.message_id)
    try:
        await context.bot.edit_message_text(chat_id=message.chat_id, message_id=message.message_id,
                                            text=f"*Transcription*:\n", parse_mode='MARKDOWN')
        await update.message.reply_text(result[0])
        await context.bot.delete_message(chat_id=file_obj_info.get("chat_id"),
                                         message_id=file_obj_info.get("message_id"))
    except sr.UnknownValueError:
        await update.message.reply_text('Sorry, I could not understand what you said.')
    except sr.RequestError as e:
        await update.message.reply_text(
            'Sorry, I could not request results from Google Speech Recognition service; {0}'.format(e))
    os.remove(file_name)  # original file is deleted
    os.remove(result[-1])  # transcription file is deleted
    logger.info("Remove %s", result[-1])


async def author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Display the author of the message """
    await update.message.reply_text(
        text="*Author*:\n"
             "↳ GitHub  : [karvanpy](https://github.com/karvanpy)\n"
             "↳ Telegram: @DensenBrad\n"
             "↳ Twitter : @DensenBrad\n\n"
             "***Contact me at @DensenBrad to request a feature or bug report***",
        parse_mode="MARKDOWN",
    )


async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Display the tutorial of the message """
    await update.message.reply_text(
        text="*How to use this bot?*\n\n"
             "1) Press /start\n"
             "2) Select the language: [INDONESIA] or [ENGLISH]\n"
             "3) Send the audio file or record it directly\n"
             "4) Wait for the process to complete\n"
             "5) The result will be sent to you!\n\n"

             "If you want to change the language from ENGLISH to INDONESIA (or vice versa):\n"
             "1) Just press /start again.\n",
        parse_mode="MARKDOWN",
    )


async def get_total_usages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Display the total number of usages """
    await update.message.reply_text(
        text=f"*Total of Transcriptions*: {context.user_data['total_usages']}",
        parse_mode="MARKDOWN",
    )


# Set up conversation handler with states and callback functions
# LO BIKIN PUSING W AJ SI
# conv_handler = ConversationHandler(
#     entry_points=[CommandHandler('start', start)],
#     states={
#         # LANGUAGE: [MessageHandler(filters.Regex('^(INDONESIA|ENGLISH)$'), language_selected)],
#         LANGUAGE: [CallbackQueryHandler(language_selected)],
#         # TRANSCRIBE: [MessageHandler(filters.VOICE | ~filters.Document.MimeType("audio/*"), transcribe_audio)],
#         TRANSCRIBE_VOICE: [MessageHandler(filters.VOICE, transcribe_voice)],
#         TRANSCRIBE_FILE: [MessageHandler(filters.Document.ALL, transcribe_file)]
#     },
#     fallbacks=[CommandHandler('cancel', cancel)]
# )


def main():
    API_TOKEN = BOT_API
    app = ApplicationBuilder().token(API_TOKEN).build()
    app.add_handler(CallbackQueryHandler(language_selected))
    app.add_handler(MessageHandler(filters.VOICE, transcribe_voice))
    app.add_handler(MessageHandler(filters.Document.AUDIO, transcribe_file))
    app.add_handler(CommandHandler("author", author))
    app.add_handler(CommandHandler("tutorial", tutorial))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_total_usages", get_total_usages))
    app.run_polling()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
        main()
