import os
import re
import django
import requests

django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    Filters, ConversationHandler
)

from decimal import Decimal
from dotenv import load_dotenv
from django.utils import timezone
from datetime import datetime, timedelta
from data.models import User, Cake, ReadyCake, LinkTracker, PromoCode

LEVEL_CHOICES = Cake.LEVEL_CHOICES
FORM_CHOICES = Cake.FORM_CHOICES
TOPPING_CHOICES = Cake.TOPPING_CHOICES
BERRIES_CHOICES = Cake.BERRIES_CHOICES
DECOR_CHOICES = Cake.DECOR_CHOICES

ADDRESS, PHONE, DELIVERY_DATE, COMMENT, CONFIRMATION, PROMO_CODE = range(6)


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
                InlineKeyboardButton('Готовые торты', callback_data='cake'),
                InlineKeyboardButton('Создать свой торт', callback_data='custom_cake')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(choice_button)
        sent_message = update.message.reply_text(
            "Выберите готовый торт или создайте свой!",
            reply_markup=reply_markup
        )
        context.user_data['ready_made_tort'] = sent_message.message_id
    else:
        pdf_path = 'agreed.pdf'
        with open(pdf_path, 'rb') as f:
            document = f.read()

        keyboard = [
            [
                InlineKeyboardButton('Согласен', callback_data='agree'),
                InlineKeyboardButton('Не согласен', callback_data='disagree')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_document(document=document,
                                      filename='file.pdf',
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
                InlineKeyboardButton('Готовые торты', callback_data='cake'),
                InlineKeyboardButton('Создать свой торт', callback_data='custom_cake')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(choice_button)
        sent_message = query.edit_message_text(text="Выберите готовый торт или создайте свой!",
                                               reply_markup=reply_markup)
        context.user_data['ready_made_tort'] = sent_message.message_id
    elif query.data == 'disagree':
        query.edit_message_text(text='Вы отказались от обработки данных. Доступ к боту ограничен.')


def order_cake(update: Update, context: CallbackContext):
    available_cakes = ReadyCake.objects.filter(is_available=True)

    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['ready_made_tort']
    )

    if not available_cakes.exists():
        update.callback_query.edit_message_text(text="К сожалению, в данный момент нет доступных тортов для заказа.")
        return

    for cake in available_cakes:
        sent_message = context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(cake.image.path, 'rb'),
            caption=f'{cake.name} - {cake.price} руб.\n\n{cake.description}\n\n{cake.ingredients}',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Заказать', callback_data=f'buy_cake_{cake.id}')]
            ])
        )
        if 'sent_messages' not in context.user_data:
            context.user_data['sent_messages'] = []
        context.user_data['sent_messages'].append(sent_message.message_id)


def buy_cake(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    cake_id = int(query.data.split('_')[2])
    cake = ReadyCake.objects.get(id=cake_id)
    context.user_data['cake_id'] = cake
    context.user_data['cake_type'] = 'ready'

    keyboard = [
        [InlineKeyboardButton('Подтвердить заказ', callback_data=f'confirm_{cake_id}')],
        [InlineKeyboardButton('Вернуться к выбору', callback_data='return_to_choice')]
    ]

    if 'sent_messages' in context.user_data:
        for message_id in context.user_data['sent_messages']:
            query.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        context.user_data['sent_messages'] = []

    query.message.reply_text(
        text=(
            f"Вы выбрали: {cake.name}\n"
            f"Цена: {cake.price} руб.\n\n"
            f"Для завершения заказа, нажмите кнопку \"Подтвердить заказ\"."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def return_to_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.bot.delete_message(chat_id=update.effective_chat.id, message_id=query.message.message_id)
    order_cake(update, context)


def confirm_order_tort(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    query.edit_message_text(text="Спасибо за ваш заказ! Теперь укажите адрес доставки:")
    return ADDRESS


def show_levels(update: Update, context: CallbackContext):
    level_buttons = [
        [InlineKeyboardButton(f'{level[1]}', callback_data=f'level_{level[0]}')] for level in LEVEL_CHOICES
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
        [InlineKeyboardButton(f'{form[1]}', callback_data=f'form_{form[0]}')] for form in FORM_CHOICES
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
        [InlineKeyboardButton(f'{topping[1]}', callback_data=f'topping_{topping[0]}')] for topping in TOPPING_CHOICES
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
        [InlineKeyboardButton(f'{berries[1]}', callback_data=f'berries_{berries[0]}')] for berries in BERRIES_CHOICES
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
        [InlineKeyboardButton(f'{decor[1]}', callback_data=f'decor_{decor[0]}')] for decor in DECOR_CHOICES
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
            InlineKeyboardButton('Пропустить', callback_data='skip_text')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = query.edit_message_text(text=text, reply_markup=reply_markup)
    context.user_data['decor_message_id'] = sent_message.message_id


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
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['decor_message_id'])
        calculate_total_price(update, context)


def skip_text(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['text_price'] = 0
    context.user_data['text'] = 'Не нужен'
    calculate_total_price(update, context)


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
    context.user_data['cake_type'] = 'custom'
    confirmation_message = (
        f"Вы выбрали торт со следующими параметрами:\n"
        f"Уровни: {level}\n"
        f"Форма: {form}\n"
        f"Топпинг: {topping}\n"
        f"Ягоды: {berries}\n"
        f"Декор: {decor}\n"
        f"Дополнительный текст: {context.user_data.get('text', 'Не указан')}\n\n"
        f"Общая стоимость: {total_price} руб.\n\n"
        f"Пожалуйста, подтвердите заказ."
    )
    keyboard = [
        [
            InlineKeyboardButton('Подтвердить', callback_data='confirm_order'),
            InlineKeyboardButton('Изменить', callback_data='change_order')
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
    query.edit_message_text(text="Спасибо за ваш заказ! Теперь укажите адрес доставки:")
    return ADDRESS


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


def request_delivery_address(update: Update, context: CallbackContext):
    context.user_data['current_state'] = 'ADDRESS'

    if update.message:
        context.user_data['address'] = update.message.text
        update.message.reply_text("Спасибо! Теперь укажите номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX:")
        return PHONE


def request_phone_number(update: Update, context: CallbackContext):
    if update.message:
        phone_number = update.message.text.strip()

        if not re.match(r'^\+?7\d{10}$|^8\d{10}$', phone_number):
            update.message.reply_text("Ошибка! Введите корректный номер: +7XXXXXXXXXX или 8XXXXXXXXXX")
            return PHONE

        if phone_number.startswith('+7'):
            phone_number = '7' + phone_number[2:]

        context.user_data['phone_number'] = phone_number
        update.message.reply_text(
            "Спасибо! Теперь укажите время и дату доставки в формате ДД.ММ.ГГГГ ЧЧ:ММ."
            " Если вам нужен торт в ближайшие 24 часа,"
            " то заказ становится срочным +20% к общей стоимости"
        )
        return DELIVERY_DATE


def request_delivery_date(update: Update, context: CallbackContext):
    if update.message:
        try:
            user_input = update.message.text.strip()
            user_datetime = datetime.strptime(user_input, "%d.%m.%Y %H:%M")
            now = datetime.now()

            if user_datetime <= now:
                update.message.reply_text(
                    "Вы указали прошедшую дату или время."
                    "Введите дату и время в будущем в формате ДД.ММ.ГГГГ ЧЧ:ММ "
                    "(например, 05.03.2025 14:30)."
                )
                return DELIVERY_DATE

            if user_datetime <= now + timedelta(hours=24):
                context.user_data['rush_order'] = True
            else:
                context.user_data['rush_order'] = False

            context.user_data['delivery_date'] = user_input
            return request_comment(update, context)
        except ValueError:
            update.message.reply_text(
                "Некорректный формат даты или времени. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 05.03.2025 14:30)."
            )
            return DELIVERY_DATE


def request_comment(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton('Пропустить', callback_data='skip_comment'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Спасибо! Теперь оставьте комментарий к заказу (необязательно):",
        reply_markup=reply_markup
    )
    return COMMENT


def add_comment(update: Update, context: CallbackContext):
    comment = update.message.text
    context.user_data['comment'] = comment
    show_confirmation_menu(update, context)
    return CONFIRMATION


def skip_comment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['comment'] = 'Не указан'
    show_confirmation_menu(update, context)
    return CONFIRMATION


def show_confirmation_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton('Подтвердить', callback_data='confirm')],
        [InlineKeyboardButton('Изменить', callback_data='change')],
        [InlineKeyboardButton('Ввести промокод', callback_data='enter_promo_code')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    confirmation_text = (
        f"Ваш заказ:\n\n"
        f"Адрес доставки: {context.user_data['address']}\n"
        f"Номер телефона: {context.user_data['phone_number']}\n"
        f"Время доставки: {context.user_data['delivery_date']}\n"
        f"Комментарий: {context.user_data.get('comment', 'Не указан')}\n\n"
        f"Выберите действие:"
    )

    if isinstance(update, Update) and update.callback_query:
        sent_message = update.callback_query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
        context.user_data['confirmation_message_id'] = sent_message.message_id
    else:
        sent_message = update.message.reply_text(text=confirmation_text, reply_markup=reply_markup)
        context.user_data['confirmation_message_id'] = sent_message.message_id
    return CONFIRMATION


def request_promo_code(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text(text="Пожалуйста, введите ваш промокод:")
    return PROMO_CODE


def process_promo_code(update: Update, context: CallbackContext):
    promo_code = update.message.text.strip()
    try:
        promo = PromoCode.objects.get(code=promo_code)

        if promo.is_valid():
            discount = promo.discount
            context.user_data['discount'] = discount
            update.message.reply_text(f"Промокод '{promo_code}' применён. Скидка: {discount}%")
        else:
            update.message.reply_text("Такого промокода нет или он более не действителен.")
    except PromoCode.DoesNotExist:
        update.message.reply_text("Промокод не найден. Пожалуйста, проверьте правильность ввода.")

    show_confirmation_menu(update, context)
    return CONFIRMATION


def confirm_order_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if 'cake_type' in context.user_data:
        cake_type = context.user_data['cake_type']
    else:
        cake_type = 'ready'

    if cake_type == 'custom':
        order_details = {
            'level': context.user_data['level'],
            'form': context.user_data['form'],
            'topping': context.user_data['topping'],
            'berries': context.user_data['berries'],
            'decor': context.user_data['decor'],
            'text': context.user_data.get('text', 'Не указан'),
            'address': context.user_data['address'],
            'phone_number': context.user_data['phone_number'],
            'delivery_date': context.user_data['delivery_date'],
            'comment': context.user_data.get('comment', 'Не указан'),
            'total_price': context.user_data['total_price']
        }
        rush_order = context.user_data.get('rush_order', False)
    else:
        cake = context.user_data['cake_id']
        order_details = {
            'cake_id': cake.id,
            'cake_name': cake.name,
            'cake_price': cake.price,
            'address': context.user_data['address'],
            'phone_number': context.user_data['phone_number'],
            'delivery_date': context.user_data['delivery_date'],
            'comment': context.user_data.get('comment', 'Не указан'),
            'total_price': cake.price,
            'cake_type': 'ready'
        }
        rush_order = context.user_data.get('rush_order', False)

    if 'discount' in context.user_data:
        discount = context.user_data['discount']
        if cake_type == 'custom':
            order_details['total_price'] = context.user_data['total_price'] * (1 - discount / 100)
        else:
            order_details['total_price'] = order_details['cake_price'] * (1 - discount / 100)

    if rush_order:
        if cake_type == 'custom':
            order_details['total_price'] = order_details['total_price'] * Decimal('1.2')
        else:
            order_details['total_price'] = order_details['total_price'] * Decimal('1.2')

    send_order_to_admin(update, context, order_details)

    if rush_order:
        rush_order_text = 'Да'
    else:
        rush_order_text = 'Нет'

    confirmation_text = (
        f"Ваш заказ подтверждён!\n\n"
        f"Адрес доставки: {context.user_data['address']}\n"
        f"Номер телефона: {context.user_data['phone_number']}\n"
        f"Время доставки: {context.user_data['delivery_date']}\n"
        f"Комментарий: {context.user_data.get('comment', 'Не указан')}\n\n"
        f"Срочный заказ: {rush_order_text}\n\n"
        f"Общая стоимость: {order_details['total_price']} руб.\n\n"
        f"Спасибо за заказ! Мы свяжемся с вами для уточнения деталей."
    )

    query.edit_message_text(text=confirmation_text)
    return ConversationHandler.END


def change_order_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['change_state'] = 'ADDRESS'
    new_text = "Введите новый адрес доставки:"
    query.edit_message_text(text=new_text)
    return ADDRESS


def send_order_to_admin(update: Update, context: CallbackContext, order_details: dict):
    user = update.effective_user
    username = user.username
    admin_chat_id = context.bot_data.get('admin_chat_id')

    if 'cake_type' in context.user_data:
        cake_type = context.user_data['cake_type']
    else:
        cake_type = 'ready'

    rush_order = context.user_data.get('rush_order', False)
    rush_order_text = 'Срочный заказ: Да' if rush_order else 'Срочный заказ: Нет'
    discount_applied = 'Да' if 'discount' in context.user_data else 'Нет'

    if cake_type == 'custom':
        admin_message = (
            f"Новый заказ от пользователя: @{username}!\n\n"
            "Заказанный торт:\n"
            f"Уровни: {order_details['level']}\n"
            f"Форма: {order_details['form']}\n"
            f"Топпинг: {order_details['topping']}\n"
            f"Ягоды: {order_details['berries']}\n"
            f"Декор: {order_details['decor']}\n"
            f"Дополнительный текст: {order_details.get('text', 'Не указан')}\n\n"
            "Информация по доставке:\n"
            f"Адрес доставки: {order_details['address']}\n"
            f"Номер телефона: {order_details['phone_number']}\n"
            f"Время доставки: {order_details['delivery_date']}\n"
            f"{rush_order_text}\n"
            f"Применён промокод?: {discount_applied}\n"
            f"Комментарий: {order_details.get('comment', 'Не указан')}\n"
            f"Общая стоимость: {order_details['total_price']} руб."
        )
    else:
        admin_message = (
            f"Новый заказ от пользователя: @{username}!\n\n"
            "Заказанный торт:\n"
            f"Название: {order_details['cake_name']}\n"
            f"Цена: {order_details['cake_price']} руб.\n\n"
            "Информация по доставки:\n"
            f"Адрес доставки: {order_details['address']}\n"
            f"Номер телефона: {order_details['phone_number']}\n"
            f"Время доставки: {order_details['delivery_date']}\n"
            f"{rush_order_text}\n"
            f"Применён промокод?: {discount_applied}\n"
            f"Комментарий: {order_details.get('comment', 'Не указан')}\n"
            f"Общая стоимость: {order_details['total_price']} руб."
        )
    context.user_data.pop('discount', None)
    context.bot.send_message(chat_id=admin_chat_id, text=admin_message)


def count_link_click(token):
    api_url = 'https://api.vk.com/method/utils.getLinkStats'
    key = 'cJdwsX'
    params = {
        'access_token': token,
        'key': key,
        'interval': 'forever',
        'extended': 1,
        'v': '5.199',
    }

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    try:
        views = response.json()['response']['stats'][0]['views']
    except Exception:
        views = 0
    link = f'https://vk.cc/{key}'
    link_tracker, created = LinkTracker.objects.get_or_create(link=link)

    if not created:
        link_tracker.click_count += views
        link_tracker.save()
    else:
        link_tracker.click_count = views
        link_tracker.save()

    return views


def main():
    load_dotenv()
    admin_chat_id = os.environ.get('ADMIN_CHAT_ID')
    updater = Updater(token=os.environ['TELEGRAM_BOT_TOKEN'], use_context=True)
    vk_token = os.environ['API_VK_TOKEN']
    count_link_click(vk_token)

    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(confirm_order, pattern='confirm_order'),
                      CallbackQueryHandler(confirm_order_tort, pattern='confirm_')],
        states={
            ADDRESS: [MessageHandler(Filters.text, request_delivery_address)],
            PHONE: [MessageHandler(Filters.text, request_phone_number)],
            DELIVERY_DATE: [MessageHandler(Filters.text, request_delivery_date)],
            COMMENT: [
                MessageHandler(Filters.text, add_comment),
                CallbackQueryHandler(skip_comment, pattern='skip_comment')
            ],
            PROMO_CODE: [MessageHandler(Filters.text, process_promo_code)],
            CONFIRMATION: [
                CallbackQueryHandler(confirm_order_user, pattern='confirm'),
                CallbackQueryHandler(change_order_user, pattern='change'),
                CallbackQueryHandler(request_promo_code, pattern='enter_promo_code')
            ]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(select_finished_or_custom, pattern='agree|disagree'))
    dp.add_handler(CallbackQueryHandler(order_cake, pattern='cake'))
    dp.add_handler(CallbackQueryHandler(buy_cake, pattern='^buy_cake_'))
    dp.add_handler(CallbackQueryHandler(return_to_choice, pattern='return_to_choice'))
    dp.add_handler(CallbackQueryHandler(confirm_order_tort, pattern='confirm_'))
    dp.add_handler(CallbackQueryHandler(show_levels, pattern='custom_cake'))
    dp.add_handler(CallbackQueryHandler(select_level, pattern='level_'))
    dp.add_handler(CallbackQueryHandler(select_form, pattern='form_'))
    dp.add_handler(CallbackQueryHandler(select_topping, pattern='topping_'))
    dp.add_handler(CallbackQueryHandler(select_berries, pattern='berries_'))
    dp.add_handler(CallbackQueryHandler(select_decor, pattern='decor_'))
    dp.add_handler(CallbackQueryHandler(skip_text, pattern='skip_text'))
    dp.add_handler(CallbackQueryHandler(confirm_order, pattern='confirm_order'))
    dp.add_handler(CallbackQueryHandler(change_order, pattern='change_order'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_text))

    updater.dispatcher.bot_data['admin_chat_id'] = admin_chat_id

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
