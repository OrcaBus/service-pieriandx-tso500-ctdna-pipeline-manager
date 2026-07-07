# Deploying a New PierianDx TSO500 ctDNA Pipeline Version

- Version: 1.0
- Contact: Alexis Lucattini, [alexisl@unimelb.edu.au](mailto:alexisl@unimelb.edu.au)

There may be times where we need to update the DAG version or panel configuration for the PierianDx TSO500 ctDNA pipeline.

Unlike ICAv2-based pipelines, version management for PierianDx involves updating the CGW DAG version and potentially the panel/project mappings rather than deploying a new CWL workflow.

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Procedure](#procedure)
  - [Step 1: Verify DAG availability in CGW UAT](#step-1-verify-dag-availability-in-cgw-uat)
  - [Step 2: Update infrastructure constants](#step-2-update-infrastructure-constants)
  - [Step 3: Test in development](#step-3-test-in-development)
  - [Step 4: Deploy to production](#step-4-deploy-to-production)
- [Workflow Manager Registration](#workflow-manager-registration)

## Overview

The PierianDx CGW uses DAG (Directed Acyclic Graph) versions to manage its analysis pipeline versions. When a new DAG version becomes available, it needs to be registered in our infrastructure constants and tested before production deployment.

It is best to engage the Velsera/PierianDx [tech support team](https://support.velsera.com/hc/en-us) when working with changes to
DAGs or PANELs. It is also critically important that any changes are done with the consultation of the curation team.

## Prerequisites

- AWS credentials configured for the target environment
- Access to the PierianDx CGW UAT environment
- Familiarity with the [infrastructure constants](../../../../infrastructure/stage/constants.ts)

## Procedure

### Step 1: Verify DAG availability in CGW UAT

Before updating the infrastructure, confirm that the new DAG version is available in the CGW UAT environment:

1. Log into the PierianDx CGW UAT portal
2. Navigate to the system settings or contact PierianDx support to confirm the DAG version is active
3. Note any new panel requirements or parameter changes associated with the new version

### Step 2: Update infrastructure constants

Update the following in [`infrastructure/stage/constants.ts`](../../../../infrastructure/stage/constants.ts):

1. Add the new DAG version to `DAG_MAP`
2. Update `DEFAULT_DAG_VERSION` if this becomes the new default
3. Update `PANEL_MAP` if panel configurations change
4. Update `PROJECT_INFO_MAP` if project type mappings change

### Step 3: Test in development

1. Create a PR with the constant updates
2. Deploy to beta via CodePipeline
3. Follow [PM.PTC.1 - Manual Pipeline Execution](../PM.PTC.1/PM.PTC.1-ManualPipelineExecution.md) to run a test case
4. Verify the case is created successfully in CGW UAT with the new DAG version
5. Confirm the informatics job completes and outputs are correct

### Step 4: Deploy to production

1. Merge the PR to `main`
2. CodePipeline will automatically deploy to beta and gamma
3. Manually promote to production by enabling the CodePipeline transition in the AWS console
4. Verify a production case runs successfully with the new version

## Workflow Manager Registration

Register the new workflow version with the Workflow Manager:

```bash
make-new-workflow.sh \
  --workflow-name 'pieriandx-tso500-ctdna' \
  --workflow-version "<new_version>" \
  --executionEngine "CGW" \
  --codeVersion "$(git rev-parse --short=7 HEAD)" \
  --validationState "VALIDATED"
```

Update the [Analysis Glue](https://github.com/OrcaBus/service-analysis-glue) constants if applicable.
