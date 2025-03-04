# project_bake_cake
Этот проект предназначен для заказа тортиков в телеграмм боте. Вы можете заказать уже готовые торты или сделать свой!

## Как установить

 - Python 3.7 или выше: Убедитесь, что у вас установлен Python. Вы можете скачать его с официального сайта.
 
### 1. Скачайте код
 - Перейдите на страницу репозитория проекта.
 - Нажмите на кнопку "Code" и выберите "Download ZIP".
### 2. Установите зависимости:
```bash
pip install -r requirements.txt
```
### 3. Получите токены:
- Получите токен vk_api.
- Создайте бота и получите его токен.
- Получите chat_id администратора (тот, кто будет модерировать).

### 4. Настройте переменные окружения:
 - Создайте файл .env в корне проекта.
 - Добавьте в него ваши API токены и chat_id администратора:
```bash
TELEGRAM_BOT_TOKEN='ваш_телеграмм_токен'
API_VK_TOKEN='ваш_api_вк_токен'
ADMIN_CHAT_ID='chat_id_администратора'
```
### 5. Создайте папки и поместите в них файлы:
- Создайте папку media.
- Поместите туда согласие на обработку данных пользователя в .pdf формате.
- Поместите туда картинки для готовых тортов.

### 6. Выполните миграции и запустите сервер:
Выполнение миграций:
```bash
python manage.py migrate
```
Запуск сервера:
```bash
python manage.py runserver
```

### 7. Настройте панель админа:
- Перейдите по ссылке добавив к ней ```/admin/```.
- Добавьте в Promo codes - произвольный промокод.
- Добавьте в Ready_cakes - готовые торты.

### 8. Запустите скрипт и начинайте работу с ботом.
Запуск скрипта:
```bash
python order_cake_telegram_bot.py
```
после этого вы можете работать с ботом для начала перейдите в него.

### Пример работы с ботом
После нажатия ```start``` вы увидите:

![Моя картинка](https://cdn.picloud.cc/b478cd9ee7215327005a30d77562e161.png)

## Цель проекта
Код написан в образовательных целях на онлайн-курсе для веб-разработчиков dvmn.org.
