#!/usr/bin/env python

# Standard imports
import typing
from typing import TypedDict

# Local imports
from . import PierianDxBaseModel

# Output dict imports
if typing.TYPE_CHECKING:
    from .medical_facility import MedicalFacilityDict


class MedicalRecordNumberDict(TypedDict):
    mrn: str
    medicalFacility: 'MedicalFacilityDict'


class MedicalRecordNumber(PierianDxBaseModel):
    mrn: str
    medical_facility: 'MedicalFacility'

    if typing.TYPE_CHECKING:
        def to_dict(self) -> MedicalRecordNumberDict:
            pass

# Local model imports at the bottom to prevent circular imports
from .medical_facility import MedicalFacility

# Then rebuild
MedicalRecordNumber.model_rebuild()
