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
        return cast(
            MedicalFacilityDict,
            cast(
                object,
                dict(filter(
                    lambda item: item[1] is not None,
                    {
                        "facility": self.facility if self.facility is not None else None,
                        "hospitalNumber": (
                            str(self.hospital_number)
                            if self.hospital_number is not None
                            else None
                        ),
                    }.items()
                ))
            )
        )
