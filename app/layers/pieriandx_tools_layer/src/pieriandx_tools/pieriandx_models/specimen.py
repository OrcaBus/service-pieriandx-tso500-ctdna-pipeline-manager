#!/usr/bin/env python3
import re
# Standard imports
import typing
from typing import Optional, Union, TypedDict, NotRequired, cast
from datetime import datetime
import pandas as pd

# Local imported attributes
from . import PierianDxBaseModel

# PierianDx literals imports
from ..pieriandx_literals import (
    EthnicityType,
    RaceType,
    GenderType,
)

# Output dict local imports
if typing.TYPE_CHECKING:
    from .medical_record_number import MedicalRecordNumberDict
    from .specimen_type import SpecimenTypeDict


# Globals
ISOFORMAT_SUFFIX = re.compile(r'([+-])(\d{2}):(\d{2})$')

class SpecimenDict(TypedDict):
    accessionNumber: str
    dateAccessioned: str
    dateReceived: str
    datecollected: str
    ethnicity: NotRequired[EthnicityType]
    externalSpecimenId: str
    name: str
    race: NotRequired[RaceType]
    gender: NotRequired[GenderType]
    hl7SpecimenId: NotRequired[str]
    type: 'SpecimenTypeDict'


class IdentifiedSpecimenDict(SpecimenDict):
    firstName: str
    lastName: str
    dateOfBirth: str
    medicalRecordNumbers: 'MedicalRecordNumberDict'


class DeIdentifiedSpecimenDict(SpecimenDict):
    studyIdentifier: str
    studySubjectIdentifier: str


# Pydantic models
class Specimen(PierianDxBaseModel):
    # Required for all specimens
    case_accession_number: str
    date_accessioned: datetime
    date_received: datetime
    date_collected: datetime
    ethnicity: Optional[EthnicityType] = None
    external_specimen_id: str
    specimen_label: str
    race: Optional[RaceType] = None
    gender: Optional[GenderType] = None
    hl_7_specimen_id: Optional[str] = None
    specimen_type: 'SpecimenType'

    def to_dict(self, **kwargs) -> SpecimenDict:
        # Initialise dict
        data = super().to_dict(**kwargs)

        # Fix accession number
        data['accessionNumber'] = data.pop('caseAccessionNumber')

        # Fix formats
        data['dateAccessioned'] = ISOFORMAT_SUFFIX.sub(
            r'\1\2\3',
            pd.to_datetime(data.pop('dateAccessioned')).isoformat(timespec='seconds'),
        )
        data['dateReceived'] = ISOFORMAT_SUFFIX.sub(
            r'\1\2\3',
            pd.to_datetime(data.pop('dateReceived')).isoformat(timespec='seconds')
        )
        # Note the typo here is intentional
        data['datecollected'] = ISOFORMAT_SUFFIX.sub(
            r'\1\2\3',
            pd.to_datetime(data.pop('dateCollected')).isoformat(timespec='seconds')
        )

        # Fix specimen type
        _ = data.pop('specimenType')
        data['type'] = self.specimen_type.to_dict()

        # Fix specimen name
        data['name'] = data.pop('specimenLabel')

        return data


class IdentifiedSpecimen(Specimen):
    # Required for Identified specimens
    first_name: str
    last_name: str
    date_of_birth: datetime
    medical_record_number: 'MedicalRecordNumber'

    def to_dict(self, **kwargs) -> IdentifiedSpecimenDict:
        # Call the parent method to get the base dictionary
        data: Union[SpecimenDict, IdentifiedSpecimenDict] = super().to_dict(**kwargs)

        # Update some of the keys to match the expected output type
        data['dateOfBirth'] = self.date_of_birth.date().isoformat()
        data['medicalRecordNumbers'] = [self.medical_record_number.to_dict()]
        return cast(
            'IdentifiedSpecimenDict',
            data
        )


class DeIdentifiedSpecimen(Specimen):
    # Required for De-Identified specimens
    study_identifier: str
    study_subject_identifier: str

    if typing.TYPE_CHECKING:
        def to_dict(self) -> DeIdentifiedSpecimenDict:
            pass


# Local model imports
# Local import at the bottom to avoid circular import issues
from .specimen_type import SpecimenType
from .medical_record_number import MedicalRecordNumber

# Rebuild the models
Specimen.model_rebuild()
IdentifiedSpecimen.model_rebuild()
DeIdentifiedSpecimen.model_rebuild()
