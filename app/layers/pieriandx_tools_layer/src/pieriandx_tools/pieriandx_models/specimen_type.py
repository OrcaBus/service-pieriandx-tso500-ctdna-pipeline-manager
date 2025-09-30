#!/usr/bin/env python3

# Standard library imports
import typing
from typing import TypedDict
from pydantic import computed_field

# Local imports
from . import PierianDxBaseModel

# Output dicts
class SpecimenTypeDict(TypedDict):
    code: str
    label: str

# Models
class SpecimenType(PierianDxBaseModel):
    # Attributes
    code: int

    @computed_field
    def label(self) -> str:
        from ..pieriandx_lookup.specimen_helpers import get_specimen_label_from_specimen_code
        return get_specimen_label_from_specimen_code(int(self.code))

    def to_dict(self, **kwargs) -> SpecimenTypeDict:
        data = super().to_dict(**kwargs)
        data['code'] = str(data['code'])

        return data
