from telebot.formatting import mlink, format_text, mbold

from model.yandexModel import YandexSearchDto


class YandexService:
    def __init__(self):
        pass

    def search_by_title(self, title: str) -> YandexSearchDto:
        return YandexSearchDto(
            search_link=f'https://music.yandex.ru/search?text={title}&type=albums'
        )

    def create_message(self, data: YandexSearchDto) -> str:
        return format_text(
            mbold('Яндекс.Музыка:'),
            mlink('Ссылка на страницу поиска', data.search_link)
        )
