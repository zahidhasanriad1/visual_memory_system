from enum import StrEnum


class ProcessingMode(StrEnum):
    FULL_VIDEO = "full_video"
    TIMELINE_SAMPLED = "timeline_sampled"
    FAST_SAMPLED = "fast_sampled"
