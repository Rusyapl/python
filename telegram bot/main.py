import telebot, wikipedia, re
import requests
import pprint
from requests.auth import AuthBase

def pogoda(message):
    class TokenAuth(AuthBase):
        """Implements a custom authentication scheme."""

        def __init__(self, token):
            self.token = token

        def __call__(self, r):
            """Attach an API token to a custom auth header."""
            r.headers['X-Yandex-API-Key'] = f'{self.token}'  # Python 3.6+
            return r

    req = requests.get(f"https://api.weather.yandex.ru/v2/forecast?lat={message.text.split()[0]}&lon={message.text.split()[1]}&limit=1&hours=false",
                       auth=TokenAuth('87a75e44-5989-43f7-9892-a0d411cee17f'))
    d = req.json()
    # print(pprint.pprint(req.json()))

    # print(d['info']['tzinfo']['name'])
    # print(d['fact']['temp'])
    t=[]
    t.append(d['info']['tzinfo']['name'])
    t.append(d['fact']['temp'])
    return t


bot = telebot.TeleBot('5960171887:AAF9gW_uK5qLSl_wvPL7xqQ-Px65FDemvRs')

@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Введите широту и долготу, чтобы получить погоду!')
# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def dolgota_shirota(message):
    print(message.text.split()[0])
    print(message.text.split()[1])
    pogoda(message)
# Запускаем бота

bot.polling(none_stop=True, interval=0)
