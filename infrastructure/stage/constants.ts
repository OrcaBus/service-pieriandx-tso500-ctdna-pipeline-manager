/* Imports */
import path from 'path';
import { DATA_SCHEMA_REGISTRY_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';
import { Dag, DagVersion, PanelName, ProjectInfo, ProjectName } from './interfaces';
import {
  ACCOUNT_ID_ALIAS,
  REGION,
  StageName,
} from '@orcabus/platform-cdk-constructs/shared-config/accounts';
import { Duration } from 'aws-cdk-lib';
import { EventBridgeRuleName } from './event-rules/interfaces';

/* Directory constants */
export const APP_ROOT = path.join(__dirname, '../../app');
export const LAMBDA_DIR = path.join(APP_ROOT, 'lambdas');
export const STEP_FUNCTIONS_DIR = path.join(APP_ROOT, 'step-functions-templates');
export const LAYERS_DIR = path.join(APP_ROOT, 'layers');
export const EVENT_SCHEMAS_DIR = path.join(APP_ROOT, 'event-schemas');

/* Workflow constants */
export const WORKFLOW_NAME = 'pieriandx-tso500-ctdna';
export const DEFAULT_PAYLOAD_VERSION = '2025.09.25';

/* Event constants */
export const EVENT_SOURCE = 'orcabus.pieriandxtso500ctdna';
export const WORKFLOW_MANAGER_EVENT_SOURCE = 'orcabus.workflowmanager';
export const DRAGEN_TSO500_CTDNA_WORKFLOW_NAME = 'dragen-tso500-ctdna';
export const WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE = 'WorkflowRunStateChange';
export const WORKFLOW_RUN_UPDATE_DETAIL_TYPE = 'WorkflowRunUpdate';

/* Status constants */
export const DRAFT_STATUS = 'DRAFT';
export const READY_STATUS = 'READY';
export const SUCCEEDED_STATUS = 'SUCCEEDED';
export const RUNNABLE_STATUS = 'RUNNABLE';

/* Monitoring constants */
export const MONITOR_RUNS_FREQUENCY = Duration.minutes(15);
export const MONITOR_EVENT_RULE_NAME: EventBridgeRuleName = 'monitorPdxRunsSchedule';

/* PierianDx Constants */
export const USER_EMAIL = 'services@umccr.org';

export const BASE_URL: Record<StageName, string> = {
  BETA: 'https://app.uat.pieriandx.com/cgw-api/v2.0.0',
  GAMMA: 'https://app.uat.pieriandx.com/cgw-api/v2.0.0',
  PROD: 'https://app.pieriandx.com/cgw-api/v2.0.0',
};

export const INSTITUTION: Record<StageName, string> = {
  BETA: 'melbournetest',
  GAMMA: 'melbournetest',
  PROD: 'melbourne',
};

export const S3_SEQUENCERRUN_ROOT: Record<StageName, string> = {
  BETA: `s3://pdx-cgwxfer-test/${INSTITUTION.BETA}/`,
  GAMMA: `s3://pdx-cgwxfer-test/${INSTITUTION.GAMMA}/`,
  PROD: `s3://pdx-xfer/${INSTITUTION.PROD}/`,
};

/* S3 Constants */
export const S3_PIERIANDX_LOOKUP_BUCKET: Record<StageName, string> = {
  BETA: `pdx-lookup-bucket-${ACCOUNT_ID_ALIAS.BETA}-${REGION}`,
  GAMMA: `pdx-lookup-bucket-${ACCOUNT_ID_ALIAS.GAMMA}-${REGION}`,
  PROD: `pdx-lookup-bucket-${ACCOUNT_ID_ALIAS.PROD}-${REGION}`,
};

/* SSM Parameter values */

// Panels
export const PANEL_MAP: Record<PanelName, string> = {
  main: 'tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne', // pragma: allowlist secret
  subpanel: 'tso500_DRAGEN_ctDNA_v2_1_subpanel_Universityofmelbourne', // pragma: allowlist secret
};
export const DEFAULT_PANEL_NAME: PanelName = 'main';

// Dags
export const DAG_MAP: Record<DagVersion, Dag> = {
  '1.0.4': {
    name: 'cromwell_tso500_ctdna_workflow_1.0.4',
    description: 'tso500_ctdna_workflow',
  },
};
export const DEFAULT_DAG_VERSION: DagVersion = '1.0.4';

export const PROJECT_INFO_MAP: Record<ProjectName, ProjectInfo> = {
  PO: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
  COUMN: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
  CUP: {
    panel: 'main',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: 285645000,
  },
  PPGL: {
    panel: 'main',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
  MESO: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
  OCEANiC: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: false,
    defaultSnomedDiseaseCode: null,
  },
  SOLACE2: {
    panel: 'main',
    sampleType: 'patientcare',
    isIdentified: false,
    defaultSnomedDiseaseCode: 55342001,
  },
  IMPARP: {
    panel: 'main',
    sampleType: 'patientcare',
    isIdentified: false,
    defaultSnomedDiseaseCode: 55342001,
  },
  Control: {
    panel: 'main',
    sampleType: 'validation',
    isIdentified: false,
    defaultSnomedDiseaseCode: 55342001,
  },
  BatchControl: {
    panel: 'main',
    sampleType: 'validation',
    isIdentified: false,
    defaultSnomedDiseaseCode: 55342001,
  },
  QAP: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
  iPredict2: {
    panel: 'subpanel',
    sampleType: 'patientcare',
    isIdentified: true,
    defaultSnomedDiseaseCode: null,
  },
};

export const PROJECT_INFO_DEFAULT: ProjectInfo = {
  panel: 'main',
  sampleType: 'patientcare',
  isIdentified: false,
  defaultSnomedDiseaseCode: 55342001,
};

// S3
export const SPECIMEN_TYPE_MAP_KEY = 'snomed/tso500_ctdna_snomed_ct_specimen_type_map.json.gz';
export const DISEASE_TREE_KEY = 'snomed/tso500_ctdna_snomed_ct_disease_tree.json.gz';
export const SNOMED_CT_SPECIMEN_TYPE_S3_PATH: Record<StageName, string> = {
  BETA: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.BETA}/${SPECIMEN_TYPE_MAP_KEY}`,
  GAMMA: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.GAMMA}/${SPECIMEN_TYPE_MAP_KEY}`,
  PROD: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.PROD}/${SPECIMEN_TYPE_MAP_KEY}`,
};
export const SNOMED_CT_DISEASE_TREE_S3_PATH: Record<StageName, string> = {
  BETA: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.BETA}/${DISEASE_TREE_KEY}`,
  GAMMA: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.GAMMA}/${DISEASE_TREE_KEY}`,
  PROD: `s3://${S3_PIERIANDX_LOOKUP_BUCKET.PROD}/${DISEASE_TREE_KEY}`,
};

/* SSM Parameter Paths */
export const SSM_PARAMETER_PATH_PREFIX = path.join(`/orcabus/workflows/${WORKFLOW_NAME}/`);

// Workflow Parameters
export const SSM_PARAMETER_PATH_WORKFLOW_NAME = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'workflow-name'
);
export const SSM_PARAMETER_PATH_PAYLOAD_VERSION = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'payload-version'
);

// PierianDx Client Paths
export const SSM_PARAMETER_PATH_PIERIANDX_USER_EMAIL = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'pieriandx-user-email'
);

export const SSM_PARAMETER_PATH_PIERIANDX_INSTITUTION = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'pieriandx-institution'
);

export const SSM_PARAMETER_PATH_PIERIANDX_BASE_URL = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'pieriandx-base-url'
);

// Sequencer Root
export const SSM_PARAMETER_PATH_SEQUENCER_ROOT = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'sequencer-root'
);

// Dag parameters
export const SSM_PARAMETER_PATH_DEFAULT_DAG_VERSION = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'default-dag-version'
);
export const SSM_PARAMETER_PATH_PREFIX_DAG_NAME_BY_DAG_VERSION_PREFIX = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'dag-name-by-dag-version'
);

// Panels
export const SSM_PARAMETER_PATH_PANEL_BY_PANEL_NAME_PREFIX = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'panel-by-panel-name-map'
);
export const SSM_PARAMETER_PATH_DEFAULT_PANEL_NAME = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'default-panel-name'
);

// Project Info
export const SSM_PARAMETER_PATH_PROJECT_INFO_BY_PROJECT_TYPE_PREFIX = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'project-info-by-project-type-map'
);
export const SSM_PARAMETER_PATH_DEFAULT_PROJECT_INFO = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  'default-project-info'
);

// S3 Paths
export const SSM_PARAMETER_PATH_S3_SPECIMEN_TYPE_MAP = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  's3-snomed-ct-specimen-type-map'
);
export const SSM_PARAMETER_PATH_S3_DISEASE_TREE = path.join(
  SSM_PARAMETER_PATH_PREFIX,
  's3-snomed-ct-disease-tree'
);

/* Schema constants */
export const SCHEMA_REGISTRY_NAME = DATA_SCHEMA_REGISTRY_NAME;
export const SSM_SCHEMA_ROOT = path.join(SSM_PARAMETER_PATH_PREFIX, 'schemas');

/* Redcap paths */
export const REDCAP_LAMBDA_FUNCTION_NAME: Record<StageName, string> = {
  BETA: 'redcap-apis-dev-lambda-function',
  GAMMA: 'redcap-apis-stg-lambda-function',
  PROD: 'redcap-apis-prod-lambda-function',
};

/* SecretManager Paths */
export const PIERIANDX_S3_CREDENTIALS_SECRET_NAME = 'PierianDx/S3Credentials'; // pragma: allowlist secret
export const PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME = 'collectPierianDxAccessToken';

/* Future proofing */
export const NEW_WORKFLOW_MANAGER_IS_DEPLOYED: Record<StageName, boolean> = {
  BETA: true,
  GAMMA: true,
  PROD: false,
};

// Used to group event rules and step functions
export const STACK_PREFIX = 'orca-pdx';
