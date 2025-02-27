import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv


def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data='agree'),
            InlineKeyboardButton("Нет", callback_data='disagree')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Привет! Для использования бота необходимо согласие на обработку данных. Вы согласны?:',
                              reply_markup=reply_markup)


def select_finished_or_custom(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'agree':
        choice_button = [
            [
                InlineKeyboardButton("Готовые торты", callback_data='cake'),
                InlineKeyboardButton("Создать свой торт", callback_data='custom_cake')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(choice_button)
        query.edit_message_text(text="Выберите готовый торт или создайте свой!:", reply_markup=reply_markup)
    elif query.data == 'disagree':
        query.edit_message_text(text='Вы отказались от обработки данных. Доступ к боту ограничен.')


def select_cake(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'cake':
        query.edit_message_text(text="Здесь будут готовые торты")
    elif query.data == 'custom_cake':
        query.edit_message_text(text="Здесь можно создать кастомный торт")


def counting_link_click():
    print("подсчёт перехода по сслыке")


def order_cake():
    print("Создаём форму для заказа готовых тортов и получаем ответ")


def order_custom_cake():
    print("Создаем форму по сборке торта и получаем ответ")


def create_order_form():
    print("Создаем форму заказа и передаем ответ заказчику")


def main():
    load_dotenv()
    updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"], use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(select_finished_or_custom, pattern='agree|disagree'))
    dp.add_handler(CallbackQueryHandler(select_cake, pattern='cake|custom_cake'))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
