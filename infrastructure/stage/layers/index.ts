import path from 'path';
import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { getPythonUvDockerImage } from '@orcabus/platform-cdk-constructs/lambda';
import { LAYERS_DIR } from '../constants';

export function buildPierianDxToolsLayer(scope: Construct): PythonLayerVersion {
  /**
        Build the pieriandx tools layer, used by a lot of different functions in this stack
    */
  return new PythonLayerVersion(scope, 'pieriandx-tools-layer', {
    entry: path.join(LAYERS_DIR, 'pieriandx_tools_layer'),
    compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
    compatibleArchitectures: [lambda.Architecture.ARM_64],
    bundling: {
      image: getPythonUvDockerImage(),
      commandHooks: {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        beforeBundling(inputDir: string, outputDir: string): string[] {
          return [];
        },
        afterBundling(inputDir: string, outputDir: string): string[] {
          return [
            `pip install ${inputDir} --target ${outputDir}`,
            `find ${outputDir} -name 'pandas' -exec rm -rf {}/tests/ \\;`,
          ];
        },
      },
    },
  });
}
