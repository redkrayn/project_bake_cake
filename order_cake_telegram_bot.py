import os
import re
import django
import requests
django.setup()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    Filters
)
from dotenv import load_dotenv
from django.utils import timezone
from data.models import User, Cake

LEVEL_CHOICES = Cake.LEVEL_CHOICES
FORM_CHOICES = Cake.FORM_CHOICES
TOPPING_CHOICES = Cake.TOPPING_CHOICES
BERRIES_CHOICES = Cake.BERRIES_CHOICES
DECOR_CHOICES = Cake.DECOR_CHOICES

LEVEL, FORM, TOPPING, BERRIES, DECOR, TEXT, CONFIRM = range(7)


def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user, created = User.objects.get_or_create(telegram_id=chat_id)
    update.message.reply_text(text='Привет, мы сказочная пекарня и делаем торты!!! \n'
                                   'Вы можете заказать у нас готовые торты, либо сделать свой. \n'
                                   'Но перед началом вам нужно зарегестрироваться!'
                              )

    if user.privacy_agreement_accepted:
        choice_button = [
            [
                InlineKeyboardButton("Готовые торты", callback_data='cake'),
                InlineKeyboardButton("Создать свой торт", callback_data='custom_cake')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(choice_button)
        update.message.reply_text(
            "Выберите готовый торт или создайте свой!",
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            text='Привет, мы сказочная пекарня и делаем торты!!!\n'
                 'Вы можете заказать у нас готовые торты, либо сделать свой.\n'
                 'Но перед началом вам нужно зарегистрироваться!'
        )
        pdf_path = "agreed.pdf"
        with open(pdf_path, 'rb') as f:
            document = f.read()

        keyboard = [
            [
                InlineKeyboardButton("Согласен", callback_data='agree'),
                InlineKeyboardButton("Не согласен", callback_data='disagree')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_document(document=document,
                                      filename="file.pdf",
                                      caption="Согласие на обработку персональных данных")

        update.message.reply_text(
            'Пожалуйста, ознакомьтесь с условиями соглашения:',
            reply_markup=reply_markup
        )


def select_finished_or_custom(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    user = User.objects.get(telegram_id=chat_id)

    if query.data == 'agree':
        user.privacy_agreement_accepted = True
        user.privacy_agreement_accepted_at = timezone.now()
        user.save()

        choice_button = [
            [
                InlineKeyboardButton("Готовые торты", callback_data='cake'),
                InlineKeyboardButton("Создать свой торт", callback_data='custom_cake')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(choice_button)
        query.edit_message_text(text="Выберите готовый торт или создайте свой!", reply_markup=reply_markup)
    elif query.data == 'disagree':
        query.edit_message_text(text='Вы отказались от обработки данных. Доступ к боту ограничен.')


def select_cake(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'cake':
        order_cake(update, context)

    elif query.data == 'custom_cake':
        query.edit_message_text(text="Выберите уровень торта:")
        show_levels(update, context)


def order_cake(update: Update, context: CallbackContext):
    image_folder = 'image_cake'
    cakes = [
        {
            'filename': 'tort1.jpg',
            'name': 'Zaher',
            'ingredients': ["соль", "вода", "мука"],
            'price': '500 руб.'
        },
        {
            'filename': 'tort2.jpg',
            'name': 'Napoleon',
            'ingredients': ["сахар", "яйца", "масло"],
            'price': '600 руб.'
        },
        {
            'filename': 'tort3.jpg',
            'name': 'Lie',
            'ingredients': ["шоколад", "молоко", "орехи"],
            'price': '700 руб.'
        }
    ]

    for cake in cakes:
        image_path = os.path.join(image_folder, cake['filename'])
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                keyboard = [
                    [
                        InlineKeyboardButton("Купить", callback_data=f'buy_{cake['name']}')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=f,
                    caption=f"*{cake['name']}*\n\nИнгредиенты: {', '.join(cake['ingredients'])}\nЦена: {cake['price']}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )


def buy_cake(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()


def show_levels(update: Update, context: CallbackContext):
    level_buttons = [
        [InlineKeyboardButton(f"{level[1]}", callback_data=f'level_{level[0]}')] for level in LEVEL_CHOICES
    ]
    reply_markup = InlineKeyboardMarkup(level_buttons)
    update.callback_query.edit_message_text(text="Выберите уровень торта:", reply_markup=reply_markup)


def select_level(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    level = int(query.data.split('_')[1])
    context.user_data['level'] = level
    query.edit_message_text(text="Выберите форму торта:")
    show_forms(update, context)


def show_forms(update: Update, context: CallbackContext):
    form_buttons = [
        [InlineKeyboardButton(f"{form[1]}", callback_data=f'form_{form[0]}')] for form in FORM_CHOICES
    ]
    reply_markup = InlineKeyboardMarkup(form_buttons)
    update.callback_query.edit_message_text(text="Выберите форму торта:", reply_markup=reply_markup)


def select_form(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    form = query.data.split('_')[1]
    context.user_data['form'] = form
    query.edit_message_text(text="Выберите топпинг для торта:")
    show_toppings(update, context)


def show_toppings(update: Update, context: CallbackContext):
    topping_buttons = [
        [InlineKeyboardButton(f"{topping[1]}", callback_data=f'topping_{topping[0]}')] for topping in TOPPING_CHOICES
    ]
    reply_markup = InlineKeyboardMarkup(topping_buttons)
    update.callback_query.edit_message_text(text="Выберите топпинг для торта:", reply_markup=reply_markup)


def select_topping(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    topping = query.data.split('_')[1]
    context.user_data['topping'] = topping
    query.edit_message_text(text="Выберите ягоды для торта:")
    show_berries(update, context)


def show_berries(update: Update, context: CallbackContext):
    berries_buttons = [
        [InlineKeyboardButton(f"{berries[1]}", callback_data=f'berries_{berries[0]}')] for berries in BERRIES_CHOICES
    ]
    reply_markup = InlineKeyboardMarkup(berries_buttons)
    update.callback_query.edit_message_text(text="Выберите ягоды для торта:", reply_markup=reply_markup)


def select_berries(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    berries = query.data.split('_')[1]
    context.user_data['berries'] = berries
    query.edit_message_text(text="Выберите декор для торта:")
    show_decor(update, context)


def show_decor(update: Update, context: CallbackContext):
    decor_buttons = [
        [InlineKeyboardButton(f"{decor[1]}", callback_data=f'decor_{decor[0]}')] for decor in DECOR_CHOICES
    ]
    reply_markup = InlineKeyboardMarkup(decor_buttons)
    update.callback_query.edit_message_text(text="Выберите декор для торта:", reply_markup=reply_markup)


def select_decor(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    decor = query.data.split('_')[1]
    context.user_data['decor'] = decor
    text = "Введите дополнительный текст для торта +500 (необязательно):"
    keyboard = [
        [
            InlineKeyboardButton("Пропустить", callback_data='skip_text')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    return TEXT


def add_text(update: Update, context: CallbackContext):
    if isinstance(update, Update) and update.message:
        text = update.message.text
    elif isinstance(update, Update) and update.callback_query:
        text = 'Не нужен'
    else:
        text = 'Не нужен'

    if text.strip() != '' and text.strip().lower() != 'не нужен':
        text_price = 500
        context.user_data['text'] = text
        context.user_data['text_price'] = text_price
        calculate_total_price(update, context)
    return CONFIRM


def skip_text(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['text_price'] = 0
    context.user_data['text'] = 'Не нужен'
    calculate_total_price(update, context)
    return CONFIRM


def calculate_total_price(update: Update, context: CallbackContext):
    level = int(context.user_data['level'])
    form = context.user_data['form']
    topping = context.user_data['topping']
    berries = context.user_data['berries']
    decor = context.user_data['decor']
    text_price = context.user_data['text_price']

    level_price = next((price for choice, price in LEVEL_CHOICES if choice == level), 0)
    form_price = next((price for choice, price in FORM_CHOICES if choice == form), 0)
    topping_price = next((price for choice, price in TOPPING_CHOICES if choice == topping), 0)
    berries_price = next((price for choice, price in BERRIES_CHOICES if choice == berries), 0)
    decor_price = next((price for choice, price in DECOR_CHOICES if choice == decor), 0)

    total_price = (int(re.sub(r'\D', '', level_price)) +
                   int(re.sub(r'\D', '', form_price)) +
                   int(re.sub(r'\D', '', topping_price)) +
                   int(re.sub(r'\D', '', berries_price)) +
                   int(re.sub(r'\D', '', decor_price)) +
                   text_price
                   )

    context.user_data['total_price'] = total_price
    confirmation_message = (
        f"Вы выбрали торт со следующими параметрами:\n"
        f"Уровни: {level}\n"
        f"Форма: {form}\n"
        f"Топпинг: {topping}\n"
        f"Ягоды: {berries}\n"
        f"Декор: {decor}\n"
        f"Дополнительный текст: {context.user_data.get('text', 'Не указан')}\n\n"
        f"Общая стоимость: {total_price} руб.\n\n"
        f"Подтвердите заказ."
    )
    keyboard = [
        [
            InlineKeyboardButton("Подтвердить", callback_data='confirm_order'),
            InlineKeyboardButton("Изменить", callback_data='change_order')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        update.callback_query.edit_message_text(text=confirmation_message, reply_markup=reply_markup)
    else:
        update.message.reply_text(text=confirmation_message, reply_markup=reply_markup)


def confirm_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_data = context.user_data

    cake = Cake(
        user=User.objects.get(telegram_id=update.effective_chat.id),
        levels=int(user_data['level']),
        form=user_data['form'],
        topping=user_data['topping'],
        berries=user_data['berries'],
        decor=user_data['decor'],
        text=user_data.get('text', ''),
        total_price=user_data['total_price'],
        delivery_date=timezone.now(),
        status='new'
    )
    cake.save()
    query.edit_message_text(text="Спасибо за ваш заказ! Мы свяжемся с вами для уточнения деталей.")


def change_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_data = context.user_data

    user_data.pop('level', None)
    user_data.pop('form', None)
    user_data.pop('topping', None)
    user_data.pop('berries', None)
    user_data.pop('decor', None)
    user_data.pop('text', None)
    user_data.pop('total_price', None)

    query.edit_message_text(text="Хорошо, давайте изменим ваш заказ. Выберите уровень торта:")
    show_levels(update, context)


def main():
    load_dotenv()
    updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"], use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(select_finished_or_custom, pattern='agree|disagree'))
    dp.add_handler(CallbackQueryHandler(select_cake, pattern='cake|custom_cake'))
    dp.add_handler(CallbackQueryHandler(select_level, pattern='level_1|level_2|level_3'))
    dp.add_handler(CallbackQueryHandler(select_form, pattern='form_circle|form_square|form_rectangle'))
    dp.add_handler(CallbackQueryHandler(select_topping,
                                        pattern='topping_none|topping_white|topping_caramel|topping_maple'
                                                '|topping_strawberry|topping_blueberry|topping_chocolate'))
    dp.add_handler(CallbackQueryHandler(select_berries,
                                        pattern='berries_none|berries_blackberry|berries_raspberry|berries_blueberry'
                                                '|berries_strawberry'))
    dp.add_handler(CallbackQueryHandler(select_decor,
                                        pattern='decor_none|decor_pistachio|decor_meringue|decor_hazelnut|decor_pecan'
                                                '|decor_marshmallow|decor_marzipan'))
    dp.add_handler(CallbackQueryHandler(skip_text, pattern='skip_text'))
    dp.add_handler(CallbackQueryHandler(confirm_order, pattern='confirm_order'))
    dp.add_handler(CallbackQueryHandler(change_order, pattern='change_order'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_text))

    updater.start_polling()
    updater.idle()


def counting_link_click(token):
    api_url = 'https://api.vk.com/method/utils.getLinkStats'
    params = {
        'access_token': token,
        'key': 'cJ7n7C',
        'interval': 'month',
        'extended': 1,
        'v': '5.199',
    }

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    views = response.json()['response']['stats'][0]['views']
    return views


if __name__ == "__main__":
    vk_token = os.environ['API_VK_TOKEN']
    main()

# def create_order_form():
#     print("Создаем форму заказа и передаем ответ заказчику")

print(counting_link_click(vk_token))

