#!/usr/bin/env python

# Standard imports
from typing import Optional, NotRequired, TypedDict, cast

# Local imports
from . import PierianDxBaseModel

class MedicalFacilityDict(TypedDict):
    facility: NotRequired[str]
    hospitalNumber: NotRequired[str]


class MedicalFacility(PierianDxBaseModel):
    facility: Optional[str] = None
    hospital_number: Optional[int] = None

    def to_dict(self, **kwargs) -> MedicalFacilityDict:
        data = super().to_dict(**kwargs)

        # Update hospital number to be a string if it exists
        if 'hospitalNumber' in data:
            data['hospitalNumber'] = str(data['hospitalNumber'])

        return cast(
            MedicalFacilityDict,
            data
        )
