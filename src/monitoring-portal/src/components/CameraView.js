import { API, graphqlOperation } from "aws-amplify";
import Container from "aws-northstar/layouts/Container";
import React, { useEffect, useState } from "react";
import ImagePanel from "./ImagePanel";
import { LoadingIndicator } from "aws-northstar";
import { initialize, fetchImage } from '../utils/s3utils'

const subscribeToNewAlarm = `subscription subscribeToNewAlarm($cameraId: String!) {
  onNewAlarm(cameraId: $cameraId) {
    cameraId
    ts
    s3url
    status
    persons {
      id
      missingMask
      missingHelmet
      faceId
    }
  }
}`;
    
const CameraViewer = () => {
  const [s3, setS3] = useState(null);
  const [img, setImg] = useState('empty');

  useEffect(() => {
    initialize().then((s3) => {
      setS3(s3);
    });
  }, []);

  useEffect(() => {
    let subscription;
    try {
      subscription = API.graphql(
        graphqlOperation(subscribeToNewAlarm, { cameraId: "kvs_example_camera_stream" })
      ).subscribe({
        next: async ({ provider, value }) => {
          console.log({ provider, value});
          const gqlSubResp = value.data.onNewFrame;
          const latestS3Key = gqlSubResp.s3url.split('/')[1];
          const ts = gqlSubResp.ts;
          console.log(latestS3Key);
          console.log(ts);
          if (s3 != null) {
            // timeDiff = 
            const imageData = await fetchImage(s3, latestS3Key);
            setImg(new Blob([imageData.buffer], { type: "image/webp" }));
          }
        },
      });
    } catch (error) {
      console.error(error);
    }
    return () => {
      subscription.unsubscribe();
    }
  }, [s3]);

  return (
    <Container>
      {
        img === 'empty' ? <LoadingIndicator label='loading' size='large' /> : <ImagePanel blob={img} />
      }
    </Container>
  );
};

export default CameraViewer;
