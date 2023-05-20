import os
import urllib.request

import cv2
import httpx
import numpy as np
import pyzbar.pyzbar
import telebot

tg_bot_token = os.environ.get('TG_BOT_TOKEN')
discogs_token = os.environ.get('DISCOGS_TOKEN')

bot = telebot.TeleBot(tg_bot_token)


@bot.message_handler(commands=['help', 'start'])
def say_welcome(message):
    bot.send_message(message.chat.id, 'start', parse_mode="markdown")


@bot.message_handler(func=lambda message: True)
def check_answer(message):
    bot.send_message(message.chat.id, 'send me barcode', parse_mode="markdown")


@bot.message_handler(content_types=["photo"])
def echo_msg(message):
    img_path = bot.get_file(message.photo[2].file_id).file_path
    detected_barcodes = download_image_and_find_barcodes(img_path)

    if not detected_barcodes:
        print("Barcode Not Detected!")
        bot.send_message(message.chat.id, 'Cant find barcode', parse_mode="markdown")
    elif len(detected_barcodes) > 1:
        print("More than 1 barcode found")
        print(detected_barcodes)
        bot.send_message(message.chat.id, 'More than 1 barcode found', parse_mode="markdown")
    else:
        print(f'Barcode found {detected_barcodes[0]}')
        discogs_response = discogs_search(detected_barcodes[0])

        youtube_link = ''
        if discogs_response['videos']:
            youtube_link = "*YouTube:*\n"
            for video in discogs_response['videos']:
                youtube_link = f"{youtube_link}[{video['title']}]({video['uri']})\n"
            youtube_link = f"{youtube_link}\n"

        text = f"*{discogs_response['title']}*\n\n" \
               f"{youtube_link}" \
               f"[Ссылка на яндекс](https://music.yandex.ru/search?text={discogs_response['title']}&type=albums)"
        print(text)

        bot.send_message(message.chat.id, text, parse_mode="markdown")


def download_image_and_find_barcodes(path):
    img_url = f'https://api.telegram.org/file/bot{tg_bot_token}/{path}'
    with urllib.request.urlopen(img_url) as response:
        img_array = np.asarray(bytearray(response.read()), dtype="uint8")
        image = cv2.imdecode(img_array, 0)
        return pyzbar.pyzbar.decode(image)


def discogs_search(barcode):
    search_response = httpx.get(
        url='https://api.discogs.com/database/search',
        params={
            'q': int(barcode.data),
            'token': discogs_token
        }
    ).json()['results'][0]
    lp_response = httpx.get(search_response['resource_url']).json()

    return {
        'title': search_response['title'],
        'cover': search_response['cover_image'],
        'url': lp_response['uri'],
        'videos': lp_response['videos'] if 'videos' in lp_response else []
    }


if __name__ == '__main__':
    bot.infinity_polling()
