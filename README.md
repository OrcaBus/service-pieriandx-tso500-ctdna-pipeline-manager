Service PierianDx TSO500 ctDNA Pipeline Manager
================================================================================

- [Template Service](#template-service)
    - [Service Description](#service-description)
        - [Name \& responsibility](#name--responsibility)
        - [Description](#description)
        - [API Endpoints](#api-endpoints)
        - [Consumed Events](#consumed-events)
        - [Published Events](#published-events)
        - [(Internal) Data states \& persistence model](#internal-data-states--persistence-model)
        - [Major Business Rules](#major-business-rules)
        - [Permissions \& Access Control](#permissions--access-control)
        - [Change Management](#change-management)
            - [Versioning strategy](#versioning-strategy)
            - [Release management](#release-management)
    - [Infrastructure \& Deployment](#infrastructure--deployment)
        - [Stateful](#stateful)
        - [Stateless](#stateless)
        - [CDK Commands](#cdk-commands)
        - [Stacks](#stacks)
    - [Development](#development)
        - [Project Structure](#project-structure)
        - [Setup](#setup)
            - [Requirements](#requirements)
            - [Install Dependencies](#install-dependencies)
            - [First Steps](#first-steps)
        - [Conventions](#conventions)
        - [Linting \& Formatting](#linting--formatting)
        - [Testing](#testing)
    - [Glossary \& References](#glossary--references)

Description
--------------------------------------------------------------------------------

### Summary

This is the PierianDx TSO500 ctDNA Pipeline Management service, responsible for managing submissions and tracking
analyses of
TSO500 to Velsera's (formerly PierianDx) [Clinical Genomics Workspace](https://app.pieriandx.com/cgw/).

While the service uses the [Workflow Manager](https://github.com/OrcaBus/service-workflow-manager) to record and receive
state changes,
and uses the similar DRAFT - READY - RUNNING - COMPLETED state model for workflow runs,
we do not use an abstracted orchestration service (such as the ICAv2 WES manager) to run the workflow,
as the CGW API already provides a high level of abstraction and management for running analyses.
Instead, this service directly interacts with the CGW API to manage cases and runs.

For each submission, the service will

* Pull necessary metadata and files from other services (e.g. Metadata Service, File Manager, RedCap)
* Upload data to Velsera's S3 bucket
* Create a case, sequencing run object and informatics job in the CGW via their API
* Track the status of the case and update the system accordingly
* Provide links to the CGW case report and vcf in the outputs.

### Ready Event Creation

![events-overview](/docs/drawio-exports/draft-to-ready.drawio.svg)

### Ready to CGW Case + Job Creation

![ready-to-case](/docs/drawio-exports/ready-to-pieriandx-case-creation.svg)

### API Endpoints

This service provides a RESTful API following OpenAPI conventions.
The Swagger documentation of the production endpoint is available here:

### Consumed Events

| Name / DetailType        | Source                    | Schema Link                                                                                                 | Description                                                      |
|--------------------------|---------------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `WorkflowRunStateChange` | `orcabus.workflowmanager` | [WorkflowRunStateChange](https://github.com/OrcaBus/wiki/tree/main/orcabus-platform#workflowrunstatechange) | Source of updates on WorkflowRuns (expected pipeline executions) |

### Published Events

| Name / DetailType     | Source                         | Schema Link   | Description                           |
|-----------------------|--------------------------------|---------------|---------------------------------------|
| `WorkflowRunUpdate` | `orcabus.pieriandxtso500ctdna` | [WorkflowRunUpdate](https://github.com/OrcaBus/wiki/blob/main/orcabus/platform/events.md#workflowrunupdate) | Reporting any updates to the pipeline state |

### Draft Event

A workflow run must be placed into a DRAFT state before it can be started.

A workflow run must be placed into a DRAFT state before it can be started.

This is to ensure that only valid workflow runs are started, and that all required data is present.

This service is responsible for both populating and validating draft workflow runs.

A draft event may even be submitted without a payload.

#### Draft Event Submission

To submit a PierianDx TSO500 ctDNA DRAFT event, please follow the [PM.PTC.1 SOP](/docs/operation/SOP/README.md#PM.PTC.1) in our SOPs documentation.

#### Draft Data Schema Validation

We have generated JSON schemas for the complete DRAFT WRU event **data** which you can find in the [`app/schemas/` directory](/app/schemas).

You can interactively check if your DRAFT event data payload matches the schema using the following links:

- [Complete DRAFT WRU Event Data Schema Page](https://www.jsonschemavalidator.net/s/4mjkB0UT)

### Release management

The service employs a fully automated CI/CD pipeline that
automatically builds and releases all changes to the `main` code branch.

### Related Services & Pipelines

#### Upstream Pipelines

- [Analysis Glue](https://github.com/OrcaBus/service-analysis-glue)
- [Dragen TSO500 ctDNA Pipeline Manager](https://github.com/OrcaBus/service-dragen-tso500-ctdna-pipeline-manager)

#### Primary Services

- [Workflow Manager](https://github.com/OrcaBus/service-workflow-manager)

#### External Services

- [RedCap APIs](https://github.com/umccr/redcap-apis)

Infrastructure & Deployment
--------------------------------------------------------------------------------

> Deployment settings / configuration (e.g. CodePipeline(s) / automated builds).

Infrastructure and deployment are managed via CDK. This template provides two types of CDK entry points: `cdk-stateless`
and `cdk-stateful`.

### CDK Commands

You can access CDK commands using the `pnpm` wrapper script.

- **`cdk-stateless`**: Used to deploy stacks containing stateless resources (e.g., AWS Lambda), which can be easily
  redeployed without side effects.
- **`cdk-stateful`**: Used to deploy stacks containing stateful resources (e.g., AWS DynamoDB, AWS RDS), where
  redeployment may not be ideal due to potential side effects.

The type of stack to deploy is determined by the context set in the `./bin/deploy.ts` file. This ensures the correct
stack is executed based on the provided context.

### Stateful Stack

The stateful stack for this service includes the following resources

- S3 Snomed Lookup bucket
- Jobs DynamoDb table
- Event Schema

To list all available stateful stacks, run:

```sh
pnpm cdk-stateful ls
```

Output:

```shell
OrcaBusStatefulPdxServiceStack
OrcaBusStatefulPdxServiceStack/PdxManagerStatefulDeploymentPipeline/OrcaBusBeta/OrcaBusStatefulPdxServiceStack (OrcaBusBeta-OrcaBusStatefulPdxServiceStack)
OrcaBusStatefulPdxServiceStack/PdxManagerStatefulDeploymentPipeline/OrcaBusGamma/OrcaBusStatefulPdxServiceStack (OrcaBusGamma-OrcaBusStatefulPdxServiceStack)
OrcaBusStatefulPdxServiceStack/PdxManagerStatefulDeploymentPipeline/OrcaBusProd/OrcaBusStatefulPdxServiceStack (OrcaBusProd-OrcaBusStatefulPdxServiceStack)
```

### Stateless Stack

The stateful stack for this service includes the following resources

- Lambdas
- StepFunctions
- Event Rules
- Event Targets

To list all available stateful stacks, run:

Output:

```shell
OrcaBusStatelessPdxServiceStack
OrcaBusStatelessPdxServiceStack/PdxManagerStatelessDeploymentPipeline/OrcaBusBeta/OrcaBusStatelessPdxServiceStack (OrcaBusBeta-OrcaBusStatelessPdxServiceStack)
OrcaBusStatelessPdxServiceStack/PdxManagerStatelessDeploymentPipeline/OrcaBusGamma/OrcaBusStatelessPdxServiceStack (OrcaBusGamma-OrcaBusStatelessPdxServiceStack)
OrcaBusStatelessPdxServiceStack/PdxManagerStatelessDeploymentPipeline/OrcaBusProd/OrcaBusStatelessPdxServiceStack (OrcaBusProd-OrcaBusStatelessPdxServiceStack)
```


Development
--------------------------------------------------------------------------------

### Project Structure

The root of the project is an AWS CDK project where the main application logic lives inside the `./app` folder.

The project is organized into the following key directories:

- **`./app`**: Contains the main application logic. You can open the code editor directly in this folder, and the
  application should run independently.

- **`./bin/deploy.ts`**: Serves as the entry point of the application. It initializes two root stacks: `stateless` and
  `stateful`. You can remove one of these if your service does not require it.

- **`./infrastructure`**: Contains the infrastructure code for the project:
    - **`./infrastructure/toolchain`**: Includes stacks for the stateless and stateful resources deployed in the
      toolchain account. These stacks primarily set up the CodePipeline for cross-environment deployments.
    - **`./infrastructure/stage`**: Defines the stage stacks for different environments:
        - **`./infrastructure/stage/config.ts`**: Contains environment-specific configuration files (e.g., `beta`,
          `gamma`, `prod`).
        - **`./infrastructure/stage/stack.ts`**: The CDK stack entry point for provisioning resources required by the
          application in `./app`.

- **`.github/workflows/pr-tests.yml`**: Configures GitHub Actions to run tests for `make check` (linting and code
  style), tests defined in `./test`, and `make test` for the `./app` directory. Modify this file as needed to ensure the
  tests are properly configured for your environment.

- **`./test`**: Contains tests for CDK code compliance against `cdk-nag`. You should modify these test files to match
  the resources defined in the `./infrastructure` folder.

### Setup

#### Requirements

```sh
node --version
v22.9.0

# Update Corepack (if necessary, as per pnpm documentation)
npm install --global corepack@latest

# Enable Corepack to use pnpm
corepack enable pnpm

```

#### Install Dependencies

To install all required dependencies, run:

```sh
make install
```

#### Update Dependencies

To update dependencies, run:

```sh
pnpm update
```

### Conventions

### Linting & Formatting

Automated checks are enforces via pre-commit hooks, ensuring only checked code is committed. For details consult the
`.pre-commit-config.yaml` file.

Manual, on-demand checking is also available via `make` targets (see below). For details consult the `Makefile` in the
root of the project.

To run linting and formatting checks on the root project, use:

```sh
make check
```

To automatically fix issues with ESLint and Prettier, run:

```sh
make fix
```

### Testing

Unit tests are available for most of the business logic. Test code is hosted alongside business in `/tests/`
directories.

```sh
make test
```

Glossary & References
--------------------------------------------------------------------------------

For general terms and expressions used across OrcaBus services, please see the
platform [documentation](https://github.com/OrcaBus/wiki/blob/main/orcabus-platform/README.md#glossary--references).
