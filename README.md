1. Телеграмм бот "HowToTranslate" развернут на удаленном сервере и доступен 
   для тестирования on-line. 
2. Работа с ботом в Telegram:
Перейдите по ссылке https://t.me/GeonavTranslatorBot 
Наберите команду /help или нажмите кнопку "Меню" и выберите команду /help и 
ознакомьтесь с инструкцией по работе с ботом.
При начале работы с ботом (команда /start или пункт "Меню" /start) для 
каждого пользователя автоматически загрузится базовый словарь из 25 слов. 
Используя кнопку "Добавить слово" можно дополнять словарь своими словами. 
3. Работа с проектом:
Создайте в postgresql новую базу данных.
Перед запуском кода в файле settings.ini расположенному в корневом каталоге 
введите имя базы данных, имя пользователя и пароль. 
Если домен и порт отличаются от установленных по-умолчанию, 
введите актуальные данные и сохраните изменения. Данные вводить без кавычек.

Установите необходимые для работы приложения модули из файла requirements. txt. 
Для того чтобы установить пакеты из requirements.txt, 
необходимо открыть командную строку, перейти в каталог проекта и 
ввести следующую команду: pip install -r requirements.txt
Если вы хотите обновить компоненты вместо их повторной установки, 
используйте команду: pip install -U -r requirements.txt.

Создайте телеграмм бота и получите токен доступа к нему.
Введите токен доступа в файл settings.ini расположенный в корневом каталоге.
Запустите код из модуля main.py.
Далее работайте с ботом в соответствии с п.1