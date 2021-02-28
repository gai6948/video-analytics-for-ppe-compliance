#!/bin/bash
npx cdk deploy --require-approval never --json true -O pipeline-output.json
codecommiturl=$(jq -r '.VideoAnalyticsPipelineStack.CodeCommitRepoSshUrl' pipeline-output.json)
git remote add codecommit $codecommiturl
# sed command to uncomment stage
git add .
git commit -m "Initial Commit"
git push -u codecommit master
