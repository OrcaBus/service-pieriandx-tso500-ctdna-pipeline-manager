# Troubleshooting

- Version: 1.0
- Contact: Alexis Lucattini, [alexisl@unimelb.edu.au](mailto:alexisl@unimelb.edu.au)

Most processes within the PierianDx TSO500 ctDNA orchestration use AWS Step Functions to manage the workflow.
We post all Step Function errors to the #alerts-prod slack channel. A staff member can then click on the offending Step Function link in the slack message to be taken to the AWS Step Functions console to investigate further.

- [Analysis Stuck in DRAFT State](#analysis-stuck-in-draft-state)
  - [Upstream Data Not Available](#upstream-data-not-available)
  - [RedCap Metadata Missing](#redcap-metadata-missing)
  - [Payload Mismatch](#payload-mismatch)
- [Analysis Stuck in READY State](#analysis-stuck-in-ready-state)
  - [S3 Upload Failure](#s3-upload-failure)
  - [CGW Case Creation Failure](#cgw-case-creation-failure)
- [Analysis Stuck in RUNNING State](#analysis-stuck-in-running-state)
  - [Monitor Not Detecting Completion](#monitor-not-detecting-completion)
- [CGW Informatics Job Failures](#cgw-informatics-job-failures)
  - [Authentication Failure](#authentication-failure)
  - [Invalid Panel or DAG Version](#invalid-panel-or-dag-version)
  - [Data Quality Issues](#data-quality-issues)

## Analysis Stuck in DRAFT State

If the analysis is stuck in DRAFT state, check the `orca-pdx--populateDraftData` state machine in the [AWS Step Functions Console](https://ap-southeast-2.console.aws.amazon.com/states/home?region=ap-southeast-2#/statemachines) for any RUNNING or FAILED executions.

### Upstream Data Not Available

The populate-draft-data state machine may be waiting for the upstream Dragen TSO500 ctDNA analysis to complete. Check:

1. Whether the upstream `dragen-tso500-ctdna` workflow run has reached SUCCEEDED status
2. Whether the glue state machine has updated the DRAFT run with upstream outputs
3. The workflow run comment in OrcaUI may indicate which fields are still missing

### RedCap Metadata Missing

If case metadata cannot be retrieved from RedCap:

1. Verify the library's subject/specimen has a RedCap record
2. Check that required fields (disease, sample type, external subject ID) are populated
3. Contact the lab team to update RedCap if metadata is missing

### Payload Mismatch

If the DRAFT event payload fails schema validation:

1. Check the most recent execution of `orca-pdx--validateDraftDataAndPutReadyEvent`
2. Look at the workflow run comments for validation errors
3. Manually update the payload and generate a new WorkflowRunUpdate DRAFT event per [SOP 1](../PM.PTC.1/PM.PTC.1-ManualPipelineExecution.md)

## Analysis Stuck in READY State

If the analysis transitions to READY but does not progress to RUNNING, check the `orca-pdx--launchPieriandxFromReadyEvent` state machine.

### S3 Upload Failure

Data upload to the PierianDx S3 transfer bucket may fail due to:

1. **Expired credentials** — The PierianDx S3 credentials in Secrets Manager may have expired. Contact PierianDx support or rotate the credentials.
2. **Transfer bucket permissions** — Verify the IAM role has write access to the PierianDx transfer bucket.
3. **File not found** — The upstream output files referenced in the payload may have been archived or deleted.

### CGW Case Creation Failure

The CGW API may reject case creation for:

1. **Invalid SNOMED mapping** — Check the SNOMED lookup bucket for the disease code
2. **Duplicate case** — A case with the same identifiers may already exist in CGW
3. **API authentication failure** — See [Authentication Failure](#authentication-failure) below

## Analysis Stuck in RUNNING State

### Monitor Not Detecting Completion

The monitor state machine runs on a schedule. If a job appears complete in CGW but the OrcaBus record hasn't updated:

1. Check the `orca-pdx--monitorPdxRuns` state machine execution history
2. Verify the scheduled EventBridge rule is enabled and triggering
3. Check if the informatics job ID in the payload matches an active job in CGW
4. If the monitor is failing, investigate the Lambda logs for API errors

## CGW Informatics Job Failures

### Authentication Failure

If the CGW API returns 401/403 errors:

1. Check the PierianDx auth token in Secrets Manager — it may have expired
2. Rotate the token via the PierianDx admin portal or contact PierianDx support
3. After rotating, redrive the failed state machine execution

### Invalid Panel or DAG Version

If CGW rejects the informatics job configuration:

1. Verify the panel code in `PANEL_MAP` is valid for the target CGW environment
2. Verify the DAG version is available (UAT vs production may have different versions)
3. Contact PierianDx support to confirm the DAG version is enabled for your organisation

### Data Quality Issues

If the informatics job fails during processing:

1. Check the job details in the CGW portal for error messages
2. Common causes include:
   - Insufficient sequencing depth (low coverage)
   - Corrupt or truncated VCF files from upstream
   - Sample contamination detected
3. If the upstream data is invalid, the Dragen TSO500 ctDNA analysis may need to be rerun

[aws_step_functions_console]: https://ap-southeast-2.console.aws.amazon.com/states/home?region=ap-southeast-2#/statemachines
