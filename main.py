import os
import urllib.request

import cv2
import httpx
import numpy as np
import pyzbar.pyzbar
import telebot
from pyzbar.wrapper import ZBarSymbol

import message_texts

# from message_texts import hello_text, on_text_received_message, cant_found_barcode_message, too_many_barcodes_message

tg_bot_token = os.environ.get('TG_BOT_TOKEN')
discogs_token = os.environ.get('DISCOGS_TOKEN')

bot = telebot.TeleBot(tg_bot_token)


@bot.message_handler(commands=['help', 'start'])
def say_welcome(message):
    bot.send_message(message.chat.id, message_texts.hello_text, parse_mode="markdown")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.reply_to(message, message_texts.on_text_received_message, parse_mode="markdown")


@bot.message_handler(content_types=['document', 'audio'])
def handle_docs_audio(message):
    bot.reply_to(message, message_texts.on_file_received_message, parse_mode="markdown")


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    detected_barcodes = find_barcodes(download_image(message))
    if not detected_barcodes:
        print("Barcode Not Detected!")
        bot.send_message(message.chat.id, message_texts.cant_found_barcode_message, parse_mode="markdown")
    elif len(detected_barcodes) > 1:
        print("More than 1 barcode found")
        print(detected_barcodes)
        bot.send_message(message.chat.id, message_texts.too_many_barcodes_message, parse_mode="markdown")
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


def download_image(message):
    image_path = bot.get_file(message.photo[3].file_id).file_path
    image_url = f'https://api.telegram.org/file/bot{tg_bot_token}/{image_path}'
    with urllib.request.urlopen(image_url) as response:
        image_array = np.asarray(bytearray(response.read()), dtype="uint8")
        return cv2.imdecode(image_array, 1)


def find_barcodes(image):
    detected_barcodes = pyzbar.pyzbar.decode(image, symbols=[ZBarSymbol.EAN13])
    if not detected_barcodes:
        thresholded_image = threshold_image(image)
        detected_barcodes_after_threshold = pyzbar.pyzbar.decode(thresholded_image, symbols=[ZBarSymbol.EAN13])
        if not detected_barcodes_after_threshold:
            rotated_image = rotate_image(thresholded_image, 45)
            detected_barcodes_after_rotate = pyzbar.pyzbar.decode(rotated_image, symbols=[ZBarSymbol.EAN13])
            detected_barcodes = detected_barcodes_after_rotate
        else:
            detected_barcodes = detected_barcodes_after_threshold

    return detected_barcodes


def threshold_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray_image, 9, 75, 75)
    _, threshold = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)
    return threshold


def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (int(w / 2), int(h / 2))
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 0.8)
    return cv2.warpAffine(image, rotation_matrix, (w, h))


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
