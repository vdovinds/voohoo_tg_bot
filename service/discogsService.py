from typing import Optional

import httpx
from telebot.formatting import format_text, mbold, mlink

from model.discogsModel import DiscogsSearchDto, VideoLink


class DiscogsService:
    def __init__(self, token):
        self.token = token

    def search_by_ean13(self, code: str) -> Optional[DiscogsSearchDto]:
        discogs_search_response = httpx.get(
            url='https://api.discogs.com/database/search',
            params={
                'q': int(code),
                'token': self.token
            }
        ).json()

        if 'results' in discogs_search_response and discogs_search_response['results']:
            result = discogs_search_response['results'][0]
            resource_response = httpx.get(result['resource_url']).json()
            videos = list(
                map(
                    lambda x: VideoLink(x['title'], x['uri']),
                    resource_response['videos'] if 'videos' in resource_response else []
                )
            )

            return DiscogsSearchDto(
                title=result['title'],
                cover=result['cover_image'],
                url=resource_response['uri'] if 'uri' in resource_response else "",
                videos=videos
            )
        else:
            return None

    def create_message(self, data: DiscogsSearchDto) -> str:
        text_list = [mbold(data.title)]
        if data.videos:
            text_list.append(self.create_youtube_part_message(data.videos))

        return '\n\n'.join(text_list)

    def create_youtube_part_message(self, videos: list) -> str:
        return format_text(
            mbold('YouTube:'),
            '\n'.join(
                map(
                    lambda x: mlink(x.title, x.url),
                    videos
                )
            )
        )
