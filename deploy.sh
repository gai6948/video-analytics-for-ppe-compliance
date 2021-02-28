#!/bin/bash
npx cdk deploy --require-approval never VideoAnalyticsInfraStack
npx cdk deploy --require-approval never GraphQLLayerStack
npx cdk deploy --require-approval never FrameProcessorStack
npx cdk deploy --require-approval never KVSFrameParserStack
