from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ConversionRequest(BaseModel):
    audio_ids: list[str] = Field(min_length=1)
    model_id: str
    pitch: int = Field(0, ge=-24, le=24)
    pitch_method: Literal["rmvpe", "fcpe", "pm"] = "rmvpe"
    index_rate: float = Field(0.75, ge=0, le=1)
    protect: float = Field(0.33, ge=0, le=0.5)
    rms_mix: float = Field(0.25, ge=0, le=1)
    speaker_id: int = Field(0, ge=0)
    separate_vocals: bool = False
    vocal_gain: float = Field(0, ge=-24, le=12)
    instrumental_gain: float = Field(0, ge=-24, le=12)
    format: Literal["wav", "flac", "mp3"] = "wav"
    sample_rate: Literal[0, 32000, 40000, 44100, 48000] = 0


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    audio_ids: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if not value.strip():
            raise ValueError("Bitte einen Namen angeben.")
        return value.strip()


class TrainingRequest(BaseModel):
    project_id: str
    epochs: int = Field(100, ge=1, le=10000)
    batch_size: int = Field(4, ge=1, le=64)
    sample_rate: Literal[32000, 40000, 48000] = 40000
    save_every: int = Field(10, ge=1, le=1000)
    learning_rate: float = Field(0.0001, ge=0.000001, le=0.001)
    pitch_method: Literal["rmvpe", "pm"] = "rmvpe"
    cache_gpu: bool = False
    resume_job_id: str | None = None
