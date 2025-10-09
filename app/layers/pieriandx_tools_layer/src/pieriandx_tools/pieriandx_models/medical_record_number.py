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

    def to_dict(self, **kwargs) -> MedicalRecordNumberDict:
        data = super().to_dict(**kwargs)

        data["medicalFacility"] = self.medical_facility.to_dict(**kwargs)

        return data

# Local model imports at the bottom to prevent circular imports
from .medical_facility import MedicalFacility

# Then rebuild
MedicalRecordNumber.model_rebuild()
