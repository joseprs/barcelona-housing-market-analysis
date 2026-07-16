from typing import Optional, Union

from pydantic import BaseModel, Field


class FlatFeatures(BaseModel):
    rooms: int = Field(..., ge=0, le=20)
    bathrooms: int = Field(..., ge=0, le=20)
    surface: float = Field(..., gt=0, le=1000)

    level8: str
    floor_desc: Optional[str] = None

    energy_letter: Optional[Union[str, int, float]] = None
    environment_letter: Optional[Union[str, int, float]] = None
    energy_value: Optional[float] = None
    environment_value: Optional[float] = None

    elevator: bool = False
    air_conditioning: bool = False
    pool: bool = False