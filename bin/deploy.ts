#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { TOOLCHAIN_ENVIRONMENT } from '@orcabus/platform-cdk-constructs/deployment-stack-pipeline';
import { StatelessDeployStack } from '../infrastructure/toolchain/stateless-stack';
import { StatefulDeployStack } from '../infrastructure/toolchain/stateful-stack';

const app = new cdk.App();

const deployMode = app.node.tryGetContext('deployMode');
if (!deployMode) {
  throw new Error("deployMode is required in context ('-c deployMode=stateless')");
}

if (deployMode === 'stateless') {
  new StatelessDeployStack(app, 'OrcaBusStatelessPdxServiceStack', {
    env: TOOLCHAIN_ENVIRONMENT,
  });
} else if (deployMode === 'stateful') {
  new StatefulDeployStack(app, 'OrcaBusStatefulPdxServiceStack', {
    env: TOOLCHAIN_ENVIRONMENT,
  });
} else {
  throw new Error("Invalid 'deployMode` set in the context");
}
