#!/usr/bin/env python3
from typing import List, Self

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from datetime import datetime, timezone


def to_utc_date(datetime_obj: datetime) -> str:
    return (
        datetime_obj.
        astimezone(timezone.utc).
        isoformat(sep="T", timespec="seconds").
        replace("+00:00", "Z")
    )


class PierianDxBaseModel(BaseModel):
    # Set the model config to use camelCase for JSON serialization
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    def model_dump(self, **kwargs):
        kwargs['by_alias'] = True

        # Iterate through attributes, if any are PierianDxBaseModels, call their model_dump method
        data_dict = super().model_dump(**kwargs)

        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, PierianDxBaseModel):
                data_dict[to_camel(field_name)] = field_value.model_dump(**kwargs)

            if isinstance(field_value, List):
                for idx, item in enumerate(field_value):
                    if isinstance(item, PierianDxBaseModel):
                        data_dict[to_camel(field_name)][idx] = item.model_dump(**kwargs)

        return data_dict

    def to_dict(self, **kwargs):
        if not kwargs:
            kwargs = {}

        # Remove 'null' values by default
        kwargs['exclude_none'] = True

        return jsonable_encoder(self.model_dump(**kwargs))
