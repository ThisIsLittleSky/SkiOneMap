from pydantic import BaseModel
from typing import List, Optional


class TrackPoint(BaseModel):
    frame: int
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    confidence: float


class TrackData(BaseModel):
    trackId: int
    className: str
    points: List[TrackPoint]


class TaskResult(BaseModel):
    taskId: int
    status: str
    tracks: Optional[List[TrackData]] = None
    trackCount: int = 0
    totalFrames: int = 0
    annotatedVideoPath: str = ""
    annotatedVideoAvailable: bool = False
    error: Optional[str] = None
