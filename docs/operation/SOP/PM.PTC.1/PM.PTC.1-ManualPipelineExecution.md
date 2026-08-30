# Manual Pipeline Execution

- Version: 2026.08.30
- Contact: Alexis Lucattini, [alexisl@unimelb.edu.au](mailto:alexisl@unimelb.edu.au)

- [Introduction](#introduction)
- [Requirements](#requirements)
- [Procedure](#procedure)
- [Confirmation](#confirmation)

## Introduction

This Pipeline Manager manages the execution of the PierianDx TSO500 ctDNA pipeline.
Here we describe the SOP for manual execution of the pipeline.

The DRAFT event generated here is intentionally minimal (workflow + libraries only), consistent
with the other OrcaBus pipeline managers. The PierianDx-specific enrichment (case metadata,
sequencer run, informatics job) is handled downstream by the populate-draft-data step function,
which is where this service diverges from the ICAv2-backed pipelines.

## Requirements

- Appropriate AWS permissions
- AWS credentials set up in the local environment
- A personal portal token, available from the OrcaBus [Portal](https://portal.umccr.org/), set as the `PORTAL_TOKEN` environment variable
- Tools installed
  - [aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) version 2 or higher
  - [jq](https://github.com/jqlang/jq) version 1.7 or higher
  - [curl](https://curl.se/download.html) version 7.76.0 or higher
  - [semver](https://github.com/fsaintjacques/semver-tool)

## Procedure

To initiate a pipeline execution we need to generate an initial DRAFT event. For more details consult the main [README](../../../../README.md).
For convenience, we provide a shell script that generates and optionally submits an appropriate event.

- Familiarise yourself with the script: [generate-WRU-draft.sh --help](./generate-WRU-draft.sh)
  - Especially check the settings in the `Globals` section
    - ensure the values are fit for your use case, e.g. for clinical samples match the accredited pipeline details
  - Set the library id(s) in the positional arguments.
- Set your portal token on the environment, e.g. `export PORTAL_TOKEN=<your-token>`
- Execute the script (e.g. `bash generate-WRU-draft.sh <library_id> --comment 'reason for run'`)
  - Note: AWS credentials need to be set on the environment
  - The `--comment` argument is required. Use it to explain the reason for the manual run; this will be recorded as a comment on the workflow run in the Portal and is helpful for future reference.
- The script should produce the JSON output of the DRAFT event that can be inspected to double check that reflects the intended request
  - Take note of the generated `workflowRunName` or `portalRunId` and the URL to the OrcaBus Portal view of the workflow.
  - You can have the script save the output json file by using the `--save-draft-payload` method.

## Confirmation

The OrcaBus [Portal](https://portal.umccr.org/) can be used to check whether the event resulted in a WorkflowRun record.

- Navigate to the Portal's WorkflowRun listing: https://portal.umccr.org/workflows/workflowRuns
- Search for your WorkflowRun using the `workflowRunName` or `portalRunId`
- Confirm that the WorkflowRun is listed and progressing as expected (check over time)
- Once the WorkflowRun has `SUCCEEDED` the results should be available via the Portal's [Files](https://portal.umccr.org/files) view
  - Simply filter by the `portalRunId`
