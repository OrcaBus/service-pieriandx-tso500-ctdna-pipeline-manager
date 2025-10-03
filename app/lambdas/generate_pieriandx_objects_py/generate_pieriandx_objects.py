#!/usr/bin/env python3

"""
Tackle workflow inputs.

By far the most complicated lambda of the lot.

Expects event input in the following syntax (how this is built is someone else's problem)

* dag: Object
  * name: string  # The name of this case dag
  * description: string  # The description of this case dag
* case_metadata: Object
  * panel_name: string  # The name of this case’s panel
  * specimen_label: string  # The mapping to the panels specimen scheme
  * sample_type: Enum  # patientcare, clinical_trial, validation, proficiency_testing
  * indication: String  # Optional input
  * disease: Object
    * code: string  # The disease id
    * label: string  # The name of the disease (optional)
  * is_identified: bool  # Boolean
  * case_accession_number: string - must be unique - uses syntax SBJID__LIBID__NNN
  * specimen_type:
    * code: string   # The SNOMED-CT term for a specimen type
    * label: Optional label for the specimen type
  * external_specimen_id: string  # The external specimen id
  * date_accessioned: Datetime  # The date the case was accessioned
  * date_collected:  Datetime  # The date the specimen was collected
  * date_received:  Datetime  # The date the specimen was received
  * gender:  Enum  # unknown, male, femail, unspecified, other, ambiguous, not_applicable
  * ethnicity:  Enum  # unknown, hispanic_or_latino, not_hispanic_or_latino, not_reported
  * race:  Enum  # american_indian_or_alaska_native, asian, black_or_african_american, native_hawaiian_or_other_pacific_islander, not_reported, unknown, white

  > Note: If the case is de-identified, the following fields are required
  * study_id:  String  # Only required if is_identified is false
  * study_subject_identifier:  String  # Only required if is_identified is false

  > Note: If the case is identified, the following fields are required
  * date_of_birth:  Datetime  # Only required if is_identified is true
  * first_name:  String  # Only required if is_identified is true
  * last_name:  String  # Only required if is_identified is true
  * medical_record_numbers:  Object  # Only required if is_identified is true
    * mrn: string  # The medical record number
    * medical_facility: Object
      * facility: string  # The name of the facility
      * hospital_number: string  # The hospital number
  * requesting_physician:  Object
    * first_name: string
    * last_name: string

* data_files:  Object
  * microsat_output:  uri
  * tmb_metrics:  uri
  * cnv:  uri
  * hard_filtered:  uri
  * fusions:  uri
  * metrics_output:  uri

* samplesheet_b64gz:  str
* instrument_run_id:  str
* portal_run_id:  str
* sequencerrun_s3_prefix:  str

We then use pydantic to validate the input and generate the following outputs

* case_creation_obj: A CaseCreation object
* sequencerrun_creation_obj: A SequencerrunCreation object
* informaticsjob_creation_obj: An InformaticsjobCreation object
* data_files: List of DataFile objects (each containing a src_uri, dest_uri and file_type)
* sequencerrun_s3_path_root: The root s3 path we will upload data to.
* This is the same as the input sequencerrun_s3_path but we will extend the run id to it
"""

# Standard imports
import logging
import pandas as pd
from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer

# Pieriandx layer imports
from pieriandx_tools.pieriandx_models.case_creation import CaseCreationType
from pieriandx_tools.pieriandx_models.dag import Dag
from pieriandx_tools.pieriandx_models.data_file import DataFile
from pieriandx_tools.pieriandx_models.disease import Disease
from pieriandx_tools.pieriandx_models.informaticsjob_creation import InformaticsjobCreation
from pieriandx_tools.pieriandx_models.medical_facility import MedicalFacility
from pieriandx_tools.pieriandx_models.medical_record_number import MedicalRecordNumber
from pieriandx_tools.pieriandx_models.physician import Physician
from pieriandx_tools.pieriandx_models.sequencerrun_creation import SequencerrunCreation
from pieriandx_tools.pieriandx_models.specimen_sequencer_info import SpecimenSequencerInfo
from pieriandx_tools.pieriandx_models.specimen_type import SpecimenType
from pieriandx_tools.utils.samplesheet_helpers import read_v2_samplesheet

TOP_LEVEL_KEYS = [
    "dag",
    "caseMetadata",
    "dataFiles",
    "panelId",
    "instrumentRunId",
    "sequencerrunS3PathRoot",
]

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def edit_samplesheet_contents(samplesheet_str: str) -> str:
    # Replace TSO500L_Data header line
    # Sample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID
    # With
    # Sample_ID,Sample_Type,Lane,index,index2,I7_Index_ID,I5_Index_ID
    # Without changing the Index1Cycles and Index2Cycles of the Reads section
    # Hacky and dirty workaround required because PierianDx is not able to handle Index / Index2 in uppercase
    # Assumes Index and Index2 fall within the middle of the index line
    return samplesheet_str.replace(',Index', ',index')


def handler(event, context):
    # Basic housekeeping
    if event is None:
        raise ValueError("Event is required")
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")

    # Check for top level keys
    if not all([key in event for key in TOP_LEVEL_KEYS]):
        logger.error(f"Could not find keys {' '.join([key for key in TOP_LEVEL_KEYS if key not in event])}")
        raise ValueError("Event is missing required top level keys")

    # Get inputs
    case_metadata = event.get("caseMetadata")
    instrument_run_id = event.get("instrumentRunId")
    case_accession_number = case_metadata.get("caseAccessionNumber")
    data_files = event.get("dataFiles", {})

    # Read samplesheet - we need this for the sequencer run infos
    v2_samplesheet_dict = read_v2_samplesheet(data_files['samplesheetUri'])

    # Collect the tso500l_data section
    if not len(v2_samplesheet_dict.get("tso500l_data")) == 1:
        logger.error("Should only be one item in the tso500l data section")
        raise ValueError

    tso500l_data_samplesheet_obj = v2_samplesheet_dict.get("tso500l_data")[0]
    sample_name = tso500l_data_samplesheet_obj['sample_id']

    if case_metadata.get("isIdentified"):
        from pieriandx_tools.pieriandx_models.case_creation import IdentifiedCaseCreation as CaseCreation
        from pieriandx_tools.pieriandx_models.specimen import IdentifiedSpecimen as Specimen
    else:
        from pieriandx_tools.pieriandx_models.case_creation import DeIdentifiedCaseCreation as CaseCreation
        from pieriandx_tools.pieriandx_models.specimen import DeIdentifiedSpecimen as Specimen

    # Other imports
    case_creation_obj: CaseCreationType
    case_creation_obj = CaseCreation(
        # Standard case collection
        dag=Dag(
            name=event.get("dag").get("name"),
            description=event.get("dag").get("description")
        ),
        disease=Disease(code=int(case_metadata.get("diseaseCode"))),
        indication=case_metadata.get("indication", None),
        panel_name=event.get("panelId"),
        sample_type=case_metadata.get("sampleType").lower(),
        # Specimen collection
        specimen=Specimen(
            # Standard specimen collection
            case_accession_number=case_accession_number,
            date_accessioned=pd.to_datetime(
                case_metadata.get("sampleReception").get("dateAccessioned"),
            ),
            date_received=pd.to_datetime(
                case_metadata.get("sampleReception").get("dateReceived"),
            ),
            date_collected=pd.to_datetime(
                case_metadata.get("sampleReception").get("dateCollected"),
            ),
            external_specimen_id=case_metadata.get("externalSpecimenId"),
            specimen_label=case_metadata.get("specimenLabel"),
            gender=case_metadata.get("gender", None),
            ethnicity=case_metadata.get("ethnicity", None),
            race=case_metadata.get("race", None),
            specimen_type=SpecimenType(code=int(case_metadata.get("specimenCode"))),
            # Identified only fields
            date_of_birth=pd.to_datetime(
                case_metadata.get("patientInformation", {}).get("dateOfBirth", None)
            ),
            first_name=case_metadata.get("patientInformation", {}).get("firstName", None),
            last_name=case_metadata.get("patientInformation", {}).get("lastName", None),
            ## Identified only
            **dict(filter(
                lambda kv_iter_: kv_iter_[1] is not None,
                {
                    "medical_record_number": MedicalRecordNumber(
                        mrn=case_metadata.get("medicalRecordNumbers").get("mrn"),
                        medical_facility=(
                            MedicalFacility(
                                facility=(
                                    case_metadata
                                    .get("medicalRecordNumbers")
                                    .get("medicalFacility")
                                    .get("facility")
                                ),
                                hospital_number=(
                                    case_metadata
                                    .get("medicalRecordNumbers")
                                    .get("medicalFacility")
                                    .get("hospitalNumber")
                                )
                            )
                        )
                    ),
                }.items() if case_metadata.get("isIdentified") else {},
            )),
            # De-identified only fields
            **dict(filter(
                lambda kv_iter_: kv_iter_[1] is not None,
                {
                    "study_identifier": case_metadata.get("study").get("id"),
                    "study_subject_identifier": case_metadata.get("study").get("subjectIdentifier")
                }.items() if not case_metadata.get("isIdentified") else {},
            )),
        ),
        # Identified fields in Case
        **dict(filter(
            lambda kv_iter_: kv_iter_[1] is not None,
            {
                "requesting_physician": Physician(
                    first_name=case_metadata.get("requestingPhysician").get("firstName"),
                    last_name=case_metadata.get("requestingPhysician").get("lastName")
                )
            }.items() if case_metadata.get("isIdentified") else {},
        )),
    )

    # Set run id (used for sequencer run path)
    run_id = "__".join(
        [
            instrument_run_id,
            case_accession_number
        ]
    )

    # Get sequencer runinfo object (used for both sequencer run and informatics job creation)
    specimen_sequencer_info = SpecimenSequencerInfo(
        run_id=run_id,
        case_accession_number=case_accession_number,
        barcode=f"{tso500l_data_samplesheet_obj.get('index')}-{tso500l_data_samplesheet_obj.get('index2')}",
        lane=tso500l_data_samplesheet_obj.get("lane", 1),
        sample_id=tso500l_data_samplesheet_obj.get("sample_id"),
        sample_type=tso500l_data_samplesheet_obj.get("sample_type")
    )

    # Sequencerrun creation object
    sequencer_run_creation = SequencerrunCreation(
        run_id=run_id,
        specimen_sequence_info=specimen_sequencer_info,
        sequencing_type="pairedEnd"
    )

    # Informatics job
    informatics_job_creation = InformaticsjobCreation(
        case_accession_number=case_accession_number,
        specimen_sequencer_run_info=specimen_sequencer_info
    )

    # Add sequencerrun path
    sequencerrun_s3_path = f"{event.get('sequencerrunS3PathRoot').rstrip('/')}/{run_id}"

    # Data files
    _ = data_files.pop("samplesheetUri", None)
    data_files = list(
        map(
            lambda data_file_iter_kv: DataFile(
                sequencerrun_path_root=sequencerrun_s3_path,
                file_type=data_file_iter_kv[0],
                sample_id=tso500l_data_samplesheet_obj.get("sample_id"),
                src_uri=data_file_iter_kv[1],
                contents=None
            ),
            data_files.items()
        )
    )
    # Add the samplesheet back in
    data_files.append(
        DataFile(
            sequencerrun_path_root=sequencerrun_s3_path,
            file_type='samplesheetContents',
            sample_id=tso500l_data_samplesheet_obj.get("sample_id"),
            src_uri=None,
            contents=edit_samplesheet_contents(str(v2_samplesheet_writer(v2_samplesheet_dict).read()))
        )
    )

    # Return list of objects for downstream sfns to consume
    return {
        "caseCreationObj": case_creation_obj.to_dict(),
        "sequencerrunCreationObj": sequencer_run_creation.to_dict(),
        "informaticsjobCreationObj": informatics_job_creation.to_dict(),
        "dataFiles": list(map(lambda data_file_iter: data_file_iter.to_dict(), data_files)),
        "sequencerrunS3Path": sequencerrun_s3_path,
        "sampleName": sample_name,
    }


#  # Idenitified Patient
# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "sequencerrun_s3_path_root": "s3://pdx-cgwxfer-test/melbournetest",
#                     "portal_run_id": "abcd1234",
#                     "samplesheet_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
#                     "panel_name": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#                     "dag": {
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "dagDescription": "tso500_ctdna_workflow"
#                     },
#                     "data_files": {
#                         "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2301368/L2301368.microsat_output.json",
#                         "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2301368/L2301368.tmb.metrics.csv",
#                         "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.cnv.vcf.gz",
#                         "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.hard-filtered.vcf.gz",
#                         "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_Fusions.csv",
#                         "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_MetricsOutput.tsv",
#                         "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                     },
#                     "case_metadata": {
#                         "isIdentified": True,
#                         "caseAccessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#                         "externalSpecimenId": "externalspecimenid",
#                         "sampleType": "PatientCare",
#                         "specimenLabel": "primarySpecimen",
#                         "indication": "Test",
#                         "diseaseCode": 64572001,
#                         "specimenCode": 122561005,
#                         "sampleReception": {
#                             "dateAccessioned": "2021-01-01",
#                             "dateCollected": "2024-02-20",
#                             "dateReceived": "2021-01-01"
#                         },
#                         "patientInformation": {
#                             "dateOfBirth": "1970-01-01",
#                             "firstName": "John",
#                             "lastName": "Doe"
#                         },
#                         "medicalRecordNumbers": {
#                             "mrn": "3069999",
#                             "medicalFacility": {
#                                 "facility": "Not Available",
#                                 "hospitalNumber": "99"
#                             }
#                         },
#                         "requestingPhysician": {
#                             "firstName": "Meredith",
#                             "lastName": "Gray"
#                         }
#                     },
#                     "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   "case_creation_obj": {
#     #     "identified": true,
#     #     "indication": "Test",
#     #     "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#     #     "sampleType": "patientcare",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "dateAccessioned": "2021-01-01T00:00:00Z",
#     #         "dateReceived": "2021-01-01T00:00:00Z",
#     #         "datecollected": "2024-02-20T00:00:00Z",
#     #         "externalSpecimenId": "externalspecimenid",
#     #         "name": "primarySpecimen",
#     #         "type": {
#     #           "code": "122561005",
#     #           "label": "Blood specimen from patient"
#     #         },
#     #         "firstName": "John",
#     #         "lastName": "Doe",
#     #         "dateOfBirth": "1970-01-01",
#     #         "medicalRecordNumbers": [
#     #           {
#     #             "mrn": "3069999",
#     #             "medicalFacility": {
#     #               "facility": "Not Available",
#     #               "hospitalNumber": "99"
#     #             }
#     #           }
#     #         ]
#     #       }
#     #     ],
#     #     "dagDescription": "tso500_ctdna_workflow",
#     #     "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#     #     "disease": {
#     #       "code": "64572001",
#     #       "label": "Disease"
#     #     },
#     #     "physicians": [
#     #       {
#     #         "firstName": "Meredith",
#     #         "lastName": "Gray"
#     #       }
#     #     ]
#     #   },
#     #   "sequencerrun_creation_obj": {
#     #     "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "barcode": "CCATCATTAG-AGAGGCAACC",
#     #         "lane": "1",
#     #         "sampleId": "L2400161",
#     #         "sampleType": "DNA"
#     #       }
#     #     ],
#     #     "type": "pairedEnd"
#     #   },
#     #   "informaticsjob_creation_obj": {
#     #     "input": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "sequencerRunInfos": [
#     #           {
#     #             "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #             "barcode": "CCATCATTAG-AGAGGCAACC",
#     #             "lane": "1",
#     #             "sampleId": "L2400161",
#     #             "sampleType": "DNA"
#     #           }
#     #         ]
#     #       }
#     #     ]
#     #   },
#     #   "data_files": [
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2301368/L2301368.microsat_output.json",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.microsat_output.json",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2301368/L2301368.tmb.metrics.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.tmb.metrics.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.cnv.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.cnv.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.hard-filtered.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.hard-filtered.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_Fusions.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161_Fusions.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_MetricsOutput.tsv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161_MetricsOutput.tsv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     }
#     #   ],
#     #   "sequencerrun_s3_path": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #   "sample_name": "L2400161"
#     # }

#
#  # De-Idenitified Patient
# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER_NAME'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['SNOMED_CT_DISEASE_TREE_S3_PATH_SSM_PARAMETER_NAME'] = '/orcabus/workflows/pieriandx-tso500-ctdna/s3-snomed-ct-disease-tree'
#     environ['SNOMED_CT_SPECIMEN_TYPE_SSM_PARAMETER_NAME'] = '/orcabus/workflows/pieriandx-tso500-ctdna/s3-snomed-ct-specimen-type-map'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "dag": {
#                         "name": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "description": "tso500_ctdna_workflow"
#                     },
#                     "caseMetadata": {
#                         "study": {
#                             "id": "Control",
#                             "subjectIdentifier": "Sera-ctDNA-Comp1pc"
#                         },
#                         "indication": "NA",
#                         "sampleType": "validation",
#                         "diseaseCode": 55342001,
#                         "isIdentified": False,
#                         "specimenCode": "122561005",
#                         "specimenLabel": "primarySpecimen",
#                         "sampleReception": {
#                             "dateReceived": "2025-09-25T16:35:48+1000",
#                             "dateCollected": "2025-09-25T16:35:48+1000",
#                             "dateAccessioned": "2025-09-25T16:35:48+1000"
#                         },
#                         "externalSpecimenId": "CMM1pc-10646259",
#                         "caseAccessionNumber": "L2500384__V2__20250925bf122452"
#                     },
#                     "dataFiles": {
#                         "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Results/L2500384/L2500384.cnv.vcf.gz",
#                         "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Results/L2500384/L2500384_Fusions.csv",
#                         "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Logs_Intermediates/Tmb/L2500384/L2500384.tmb.metrics.csv",
#                         "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
#                         "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Results/L2500384/L2500384_MetricsOutput.tsv",
#                         "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Logs_Intermediates/DragenCaller/L2500384/L2500384.microsat_output.json",
#                         "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Results/L2500384/L2500384.hard-filtered.vcf.gz"
#                     },
#                     "panelId": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#                     "instrumentRunId": "250328_A01052_0258_AHFGM7DSXF",
#                     "sequencerrunS3PathRoot": "s3://pdx-cgwxfer-test/melbournetest/"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     Yields
#     {
#       "case_creation_obj": {
#         "identified": false,
#         "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#         "sampleType": "patientcare",
#         "specimens": [
#           {
#             "accessionNumber": "L2400160__V2__20241003f44a5496",
#             "dateAccessioned": "2024-10-03T00:00:00Z",
#             "dateReceived": "2024-10-03T00:00:00Z",
#             "datecollected": "2024-10-03T00:00:00Z",
#             "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#             "name": "primarySpecimen",
#             "type": {
#               "code": "122561005",
#               "label": "Blood specimen from patient"
#             },
#             "studyIdentifier": "Testing",
#             "studySubjectIdentifier": "CMM1pc-10646259ilm"
#           }
#         ],
#         "dagDescription": "tso500_ctdna_workflow",
#         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#         "disease": {
#           "code": "55342001",
#           "label": "Neoplastic disease"
#         }
#       },
#       "sequencerrun_creation_obj": {
#         "runId": "240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#         "specimens": [
#           {
#             "accessionNumber": "L2400160__V2__20241003f44a5496",
#             "barcode": "AGAGGCAACC-CCATCATTAG",
#             "lane": "1",
#             "sampleId": "L2400160",
#             "sampleType": "DNA"
#           }
#         ],
#         "type": "pairedEnd"
#       },
#       "informaticsjob_creation_obj": {
#         "input": [
#           {
#             "accessionNumber": "L2400160__V2__20241003f44a5496",
#             "sequencerRunInfos": [
#               {
#                 "runId": "240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#                 "barcode": "AGAGGCAACC-CCATCATTAG",
#                 "lane": "1",
#                 "sampleId": "L2400160",
#                 "sampleType": "DNA"
#               }
#             ]
#           }
#         ]
#       },
#       "data_files": [
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/DragenCaller/L2400160/L2400160.microsat_output.json",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.microsat_output.json",
#           "needs_decompression": false,
#           "contents": null
#         },
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/Tmb/L2400160/L2400160.tmb.metrics.csv",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.tmb.metrics.csv",
#           "needs_decompression": false,
#           "contents": null
#         },
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.cnv.vcf.gz",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.cnv.vcf",
#           "needs_decompression": true,
#           "contents": null
#         },
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.hard-filtered.vcf.gz",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.hard-filtered.vcf",
#           "needs_decompression": true,
#           "contents": null
#         },
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_Fusions.csv",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160_Fusions.csv",
#           "needs_decompression": false,
#           "contents": null
#         },
#         {
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_MetricsOutput.tsv",
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160_MetricsOutput.tsv",
#           "needs_decompression": false,
#           "contents": null
#         }
#       ],
#       "sequencerrun_s3_path": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#       "sample_name": "L2400160"
#     }

# PROD
# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-production"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "sequencerrun_s3_path_root": "s3://pdx-cgwxfer/melbourne",
#                     "portal_run_id": "20241105f6bc3fb9",
#                     "samplesheet_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
#                     "panel_name": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#                     "dag": {
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "dagDescription": "tso500_ctdna_workflow"
#                     },
#                     "data_files": {
#                         "microsatOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/DragenCaller/L2401560/L2401560.microsat_output.json",
#                         "tmbMetricsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/Tmb/L2401560/L2401560.tmb.metrics.csv",
#                         "cnvVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560.cnv.vcf.gz",
#                         "hardFilteredVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560.hard-filtered.vcf.gz",
#                         "fusionsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_Fusions.csv",
#                         "metricsOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_MetricsOutput.tsv",
#                         "samplesheetUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                     },
#                     "case_metadata": {
#                         "isIdentified": False,
#                         "caseAccessionNumber": "L2401560__V2__20241105f6bc3fb9",
#                         "externalSpecimenId": "0042-61203",
#                         "sampleType": "patientcare",
#                         "specimenLabel": "primarySpecimen",
#                         "indication": "NA",
#                         "diseaseCode": 254637007,
#                         "specimenCode": "122561005",
#                         "sampleReception": {
#                             "dateAccessioned": "2024-11-05T16:11:36+1100",
#                             "dateCollected": "2024-10-23T23:00:00+1100",
#                             "dateReceived": "2024-10-24T00:00:00+1100"
#                         },
#                         "study": {
#                             "id": "OCEANiC",
#                             "subjectIdentifier": "0042-61203"
#                         }
#                     },
#                     "instrument_run_id": "241101_A01052_0236_BHVJNMDMXY"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   "case_creation_obj": {
#     #     "identified": false,
#     #     "indication": "NA",
#     #     "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#     #     "sampleType": "patientcare",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "L2401560__V2__20241105f6bc3fb9",
#     #         "dateAccessioned": "2024-11-05T05:11:36Z",
#     #         "dateReceived": "2024-10-23T13:00:00Z",
#     #         "datecollected": "2024-10-23T12:00:00Z",
#     #         "externalSpecimenId": "0042-61203",
#     #         "name": "primarySpecimen",
#     #         "type": {
#     #           "code": "122561005",
#     #           "label": "Blood specimen from patient"
#     #         },
#     #         "studyIdentifier": "OCEANiC",
#     #         "studySubjectIdentifier": "0042-61203"
#     #       }
#     #     ],
#     #     "dagDescription": "tso500_ctdna_workflow",
#     #     "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#     #     "disease": {
#     #       "code": "254637007",
#     #       "label": "Non-small cell lung cancer"
#     #     }
#     #   },
#     #   "sequencerrun_creation_obj": {
#     #     "runId": "241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "L2401560__V2__20241105f6bc3fb9",
#     #         "barcode": "ATTCAGAA-AGGCTATA",
#     #         "lane": "1",
#     #         "sampleId": "L2401560",
#     #         "sampleType": "DNA"
#     #       }
#     #     ],
#     #     "type": "pairedEnd"
#     #   },
#     #   "informaticsjob_creation_obj": {
#     #     "input": [
#     #       {
#     #         "accessionNumber": "L2401560__V2__20241105f6bc3fb9",
#     #         "sequencerRunInfos": [
#     #           {
#     #             "runId": "241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9",
#     #             "barcode": "ATTCAGAA-AGGCTATA",
#     #             "lane": "1",
#     #             "sampleId": "L2401560",
#     #             "sampleType": "DNA"
#     #           }
#     #         ]
#     #       }
#     #     ]
#     #   },
#     #   "data_files": [
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/DragenCaller/L2401560/L2401560.microsat_output.json",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560.microsat_output.json",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Logs_Intermediates/Tmb/L2401560/L2401560.tmb.metrics.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560.tmb.metrics.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560.cnv.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560.cnv.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560.hard-filtered.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560.hard-filtered.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_Fusions.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560_Fusions.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_MetricsOutput.tsv",
#     #       "dest_uri": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560_MetricsOutput.tsv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     }
#     #   ],
#     #   "sequencerrun_s3_path": "s3://pdx-cgwxfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9",
#     #   "sample_name": "L2401560"
#     # }
