import { SsmParameterPaths, SsmParameterValues } from './ssm/interfaces';

export type DagVersion = '1.0.4';

export type PanelName = 'main' | 'subpanel';

export interface Dag {
  name: string;
  description: string;
}

export type ProjectName =
  | 'PO'
  | 'COUMN'
  | 'CUP'
  | 'PPGL'
  | 'MESO'
  | 'OCEANiC'
  | 'SOLACE2'
  | 'IMPARP'
  | 'Control'
  | 'BatchControl'
  | 'QAP'
  | 'iPredict2';

export interface ProjectInfo {
  panel: string;
  sampleType: string;
  isIdentified: boolean;
  defaultSnomedDiseaseCode: number | null;
}

/**
 * Stateful application stack interface.
 */

export interface StatefulApplicationStackConfig {
  // Values
  // Detail
  ssmParameterValues: SsmParameterValues;

  // Keys
  ssmParameterPaths: SsmParameterPaths;

  // Bucket
  lookupBucketName: string;
}

/**
 * Stateless application stack interface.
 */
export interface StatelessApplicationStackConfig {
  // Event Stuff
  eventBusName: string;

  // Workflow manager stuff
  isNewWorkflowManagerDeployed: boolean;

  // SSM Parameter paths
  ssmParameterPaths: SsmParameterPaths;

  // Redcap lambda name
  redcapLambdaName: string;

  // S3 Bucket
  lookupBucketName: string;
}
