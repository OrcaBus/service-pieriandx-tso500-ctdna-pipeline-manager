#!/usr/bin/env python3

# Standard imports
import typing
from typing import TypedDict, List

# Local imports
from . import PierianDxBaseModel

# Specimen Sequencer Info
from ..pieriandx_literals import SequencingType

# Output dict imports
if typing.TYPE_CHECKING:
    from .specimen_sequencer_info import SequencerRunInfoDict


class SequencerrunCreationDict(TypedDict):
    runId: str
    specimens: List['SequencerRunInfoDict']
    type: str


class SequencerrunCreation(PierianDxBaseModel):
    # Sequencer run information
    run_id: str
    specimen_sequence_info: 'SpecimenSequencerInfo'
    sequencing_type: SequencingType

    def to_dict(self, **kwargs) -> SequencerrunCreationDict:
        data = super().to_dict(**kwargs)

        del data['specimenSequenceInfo']

        data['specimens'] = [self.specimen_sequence_info.to_dict(**kwargs)]
        data['type'] = data.pop('sequencingType')

        return data


# Local model imports
# Import at the bottom to prevent circular imports
from .specimen_sequencer_info import SpecimenSequencerInfo
SequencerrunCreation.model_rebuild()
