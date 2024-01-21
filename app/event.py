# -*- coding: utf-8 -*-
# @Time    : 2023/12/10 下午10:33
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm
from io import TextIOBase
from typing import Union, IO, List, Optional

from anime_identify import AnimeIDF
from loguru import logger
from pydantic import BaseModel

from app.utils import WdTaggerSDK
from setting.wdtagger import TaggerSetting

ANIME = AnimeIDF()


class CensorResult(BaseModel):
    anime_score: float
    risk_tag: Optional[List[str]] = []
    anime_tags: Optional[List[str]] = []


def build_risk_tag(tags):
    _risk = []
    if "loli" in tags:
        _risk.append("loli")
    if "6+girls" in tags:
        _risk.append("6+girls")
    if "multiple_girls" in tags:
        _risk.append("multiple_girls")
    if "censored" in tags:
        _risk.append("censored")
    return _risk


async def pipeline_pass(trace_id, content: Union[IO, TextIOBase]) -> CensorResult:
    content.seek(0)
    anime_score = ANIME.predict_image(content=content)
    if anime_score > 50:
        logger.info(f"Censored {trace_id},score {anime_score}")
        return CensorResult(anime_score=anime_score)
    content.seek(0)
    raw_output_wd = await WdTaggerSDK(base_url=TaggerSetting.wd_api_endpoint).upload(
        file=content.read(),
        token="censor",
        general_threshold=0.5,
        character_threshold=0.85,
    )
    content.close()
    tag_result: dict = raw_output_wd["general_res"]
    risk_tag = build_risk_tag(tags=tag_result)
    anime_tag = list(tag_result.keys())
    logger.info(f"Censored {trace_id},score {anime_score},result {tag_result}")
    return CensorResult(
        anime_score=anime_score, risk_tag=risk_tag, anime_tags=anime_tag
    )
