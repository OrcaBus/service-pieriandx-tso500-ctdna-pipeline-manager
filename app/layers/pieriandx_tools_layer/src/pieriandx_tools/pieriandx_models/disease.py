#!/usr/bin/env python3

# Standard library imports
import typing
from typing import Optional, TypedDict

from pydantic import computed_field

# Local imports
from . import PierianDxBaseModel


# Output class
class DiseaseDict(TypedDict):
    code: str
    label: str


class Disease(PierianDxBaseModel):
    # Attributes
    code: int

    @computed_field
    def label(self) -> Optional[str]:
        # Local imports
        from ..pieriandx_lookup.disease_helpers import get_disease_label_from_disease_code
        return get_disease_label_from_disease_code(int(self.code))

    def to_dict(self, **kwargs) -> DiseaseDict:
        data = super().to_dict(**kwargs)

        # Fix code
        data['code'] = str(data['code'])

        return data
