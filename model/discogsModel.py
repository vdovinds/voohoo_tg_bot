from dataclasses import dataclass


@dataclass(frozen=True)
class DiscogsSearchDto:
    title: str
    cover: str
    url: str
    videos: list


@dataclass(frozen=True)
class VideoLink:
    title: str
    url: str
