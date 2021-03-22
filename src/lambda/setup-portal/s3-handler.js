const mime = require("mime-types");
const unzip = require("unzipper");

const {
  COGNITO_IDENTITY_POOL,
  COGNITO_USERPOOL_ID,
  COGNITO_USERPOOLCLIENT_ID,
  FILE_BUCKET,
  FROM_BUCKET,
  REGION,
  FRAME_BUCKET,
  VERSION,
  GQL_ENDPOINT,
} = process.env;

const CONFIG_FILENAME = "settings.js";
const FRONTEND_PATH = `ppe-monitoring-portal/ui-portal-v${VERSION}.zip`;

const ACL = "private";

module.exports = (s3) => {
  const deleteFile = (params) => s3.deleteObject(params).promise();
  const listFiles = (params) => s3.listObjects(params).promise();
  const upload = (params) => s3.upload(params).promise();

  return {
    copyFiles: () => {
        console.log(`Downloading s3://${FROM_BUCKET}/${FRONTEND_PATH}`);
        unzip.Open.s3(s3, { Bucket: FROM_BUCKET, Key: FRONTEND_PATH })
        .then((directory) =>
          directory.files.filter((x) => x.type !== "Directory")
        )
        .then((files) =>
          files.map((file) =>
            upload({
              ACL,
              Body: file.stream(),
              Bucket: FILE_BUCKET,
              ContentType: mime.lookup(file.path) || "application/octet-stream",
              Key: file.path,
            })
          )
        )
        .then((ps) => Promise.all(ps))
        .then(() => console.log("Directory unzipped to S3"))
    },
    removeFiles: () =>
      listFiles({
        Bucket: FILE_BUCKET,
      }).then((result) =>
        Promise.all(
          result.Contents.map((file) => file.Key).map((file) =>
            deleteFile({
              Bucket: FILE_BUCKET,
              Key: file,
            })
          )
        )
      ),

    writeSettings: () =>
      s3
        .putObject({
          ACL,
          Bucket: FILE_BUCKET,
          Key: CONFIG_FILENAME,
          Body: `window.s3PortalSettings = ${JSON.stringify({
            identityPoolId: COGNITO_IDENTITY_POOL,
            userPoolId: COGNITO_USERPOOL_ID,
            userPoolWebClientId: COGNITO_USERPOOLCLIENT_ID,
            frameBucketName: FRAME_BUCKET,
            region: REGION,
            graphqlEndpoint: GQL_ENDPOINT,
          })};`,
        })
        .promise(),
  };
};
