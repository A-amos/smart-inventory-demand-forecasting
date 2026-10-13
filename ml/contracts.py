from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class ForecastPoint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    forecast_date: date
    horizon_day: int = Field(ge=1, le=28, strict=True)
    predicted_demand: Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ForecastOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['forecast-v1'] = 'forecast-v1'
    source_namespace: Literal['uci-online-retail-ii'] = 'uci-online-retail-ii'
    sku: str = Field(min_length=1, max_length=64)
    forecast_origin: date
    horizon_days: int = Field(ge=1, le=28, strict=True)
    model_id: str = Field(min_length=1)
    model_version: Literal['retail-demand-v1'] = 'retail-demand-v1'
    trained_through: date
    created_at: AwareDatetime
    points: list[ForecastPoint]

    @model_validator(mode='after')
    def consistent_dates(self):
        from datetime import timedelta
        if self.trained_through > self.forecast_origin:
            raise ValueError('Forecast origin must not predate model training cutoff')
        if len(self.points) != self.horizon_days:
            raise ValueError('One point per forecast day required')
        for index, point in enumerate(self.points, 1):
            if point.horizon_day != index or point.forecast_date != self.forecast_origin + timedelta(days=index):
                raise ValueError('Forecast dates/horizon steps must follow the origin consecutively')
        return self
