# Updating SSM Parameters

- Version: 1.0
- Contact: Alexis Lucattini, [alexisl@unimelb.edu.au](mailto:alexisl@unimelb.edu.au)

From time to time there may be a requirement to update SSM parameters for the PierianDx TSO500 ctDNA pipeline. This includes updating DAG versions, panel mappings, project info, or other configuration values managed via AWS Systems Manager Parameter Store.

- [Overview](#overview)
- [Constants File Update](#constants-file-update)
- [Draft Event Schema](#draft-event-schema)
- [Testing](#testing)

## Overview

All SSM parameters for this service live under the prefix `/orcabus/workflows/pieriandx-tso500-ctdna/`. These parameters are defined in the CDK infrastructure and deployed via CodePipeline. Direct manual edits to SSM parameters in the console should be avoided — instead, update the infrastructure code.

Key parameters include:

| Parameter                      | Purpose                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| `default-dag-version`          | The default PierianDx DAG version used for new analyses        |
| `panel-map`                    | JSON mapping of assay types to PierianDx panel identifiers     |
| `project-info-map`             | JSON mapping of specimen/project types to CGW project settings |
| `pieriandx-s3-credentials-arn` | ARN of the Secrets Manager secret for S3 transfer              |
| `pieriandx-auth-token-arn`     | ARN of the Secrets Manager secret for CGW API auth             |

## Constants File Update

To update parameters, modify the [infrastructure constants file](../../../../infrastructure/stage/constants.ts).

Common updates include:

- **Adding a new panel**: Update `PANEL_MAP` with the new panel identifier and its associated settings
- **Changing the default DAG version**: Update `DEFAULT_DAG_VERSION`
- **Updating project info**: Modify `PROJECT_INFO_MAP` for new specimen type/project mappings

After updating, create a PR and deploy via the normal CI/CD pipeline.

## Draft Event Schema

If you are adding or removing parameters that affect the DRAFT payload structure, you may need to update the [draft event schema](../../../../app/event-schemas/complete-data-draft/2025.09.25/complete-data-draft-schema.json) to reflect these changes.
Breaking changes will require a new event schema version.

## Testing

1. Deploy changes to beta via CodePipeline
2. Follow the [Manual Pipeline Execution SOP](../PM.PTC.1/PM.PTC.1-ManualPipelineExecution.md) to trigger a test run
3. Verify the updated parameters are being used correctly in the populate-draft-data state machine
4. Check the CGW UAT to confirm the case was created with the correct settings
5. Once validated, promote to production

See the [Workflow Validation SOP](../PM.PTC.4/PM.PTC.4-RunningWorkflowValidations.md) for a more comprehensive validation procedure.
