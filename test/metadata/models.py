import datetime
from api_toolkit.define.model import BaseModel, Field
import uuid
from sqlalchemy import UUID, Integer, String, DateTime, Float
from api_toolkit.define.link import OneManyLink, ManyManyLink


class VideoStudy(BaseModel):
    class TKConfig:
        title = '视频学习项目'
        links = [
            ManyManyLink('VideoStudy', 'Video'),
        ]

    id = Field(uuid.UUID, UUID, primary_key=True, default_factory=uuid.uuid4)
    name = Field(str, String(255), default='')


class Video(BaseModel):
    class TKConfig:
        title = '视频'
        links = [
            OneManyLink('Video', 'Sentence'),
            OneManyLink('Video', 'VideoRecord'),
        ]

    id = Field(uuid.UUID, UUID, primary_key=True, default_factory=uuid.uuid4)
    name = Field(str, String(255), default='')
    type = Field(int, Integer, default=0)
    video_id = Field(uuid.UUID, UUID)


class Sentence(BaseModel):
    class TKConfig:
        title = '分句'

    id = Field(uuid.UUID, UUID, primary_key=True, default_factory=uuid.uuid4)
    index = Field(int, Integer, default=0)
    text = Field(str, String(255), default='')
    sound_id = Field(uuid.UUID, UUID)


class VideoRecord(BaseModel):
    class TKConfig:
        title = '视频测试记录'

    id = Field(uuid.UUID, UUID, primary_key=True, default_factory=uuid.uuid4)
    score = Field(float, Float, default=0)
    test_type = Field(int, Integer, default=0)
    res_img = Field(uuid.UUID, UUID)
    created_at = Field(datetime.datetime, DateTime, default_factory=datetime.datetime.now)
