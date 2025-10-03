#!/usr/bin/env python3

import typing
from typing import TypedDict, cast, Union

# Local imports
from . import PierianDxBaseModel
from ..pieriandx_literals import SequencingSampleType

# Output models
class SequencerRunInfoDict(TypedDict):
    accessionNumber: str
    barcode: str
    lane: str
    sampleId: str
    sampleType: SequencingSampleType

class SequencerRunInfoJobDict(TypedDict):
    barcode: str
    lane: str
    runId: str
    sampleId: str
    sampleType: SequencingSampleType


class SpecimenSequencerInfo(PierianDxBaseModel):
    run_id: str
    case_accession_number: str
    barcode: str
    lane: int
    sample_id: str
    sample_type: SequencingSampleType

    def to_dict(self, **kwargs) -> SequencerRunInfoDict:
        # Get data from dump
        data = super().to_dict(**kwargs)

        # Rename case_accession_number to accessionNumber
        data['accessionNumber'] = data.pop('caseAccessionNumber')

        # Convert lane to string
        data['lane'] = str(data['lane'])

        # Remove run_id as it's not needed in this context
        _ = data.pop('runId')

        return cast(SequencerRunInfoDict, data)

    def to_informaticsjob_dict(self, **kwargs) -> SequencerRunInfoJobDict:
        # Get data from dump
        data: Union[SequencerRunInfoDict, SequencerRunInfoJobDict] = super().to_dict(**kwargs)

        # Remove case_accession_number as it's not needed in this context
        _ = data.pop('caseAccessionNumber')

        # Convert lane to string
        data['lane'] = str(data['lane'])

        # Reinsert run_id as runId
        data['runId'] = self.run_id

        return cast('SequencerRunInfoJobDict', data)
