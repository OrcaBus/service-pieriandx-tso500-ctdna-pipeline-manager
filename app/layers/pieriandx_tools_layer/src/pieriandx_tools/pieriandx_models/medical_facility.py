#!/usr/bin/env python

# Standard imports
import typing
from typing import Optional, NotRequired, TypedDict

# Local imports
from . import PierianDxBaseModel

class MedicalFacilityDict(TypedDict):
    facility: NotRequired[str]
    hospitalNumber: NotRequired[str]


class MedicalFacility(PierianDxBaseModel):
    facility: Optional[str] = None
    hospital_number: Optional[str] = None

    if typing.TYPE_CHECKING:
        def to_dict(self, **kwargs) -> MedicalFacilityDict:
            pass
