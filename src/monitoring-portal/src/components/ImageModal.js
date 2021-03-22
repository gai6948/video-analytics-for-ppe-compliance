import { useState } from "react";
import { Button, Modal } from "aws-northstar/components";
import Container from "aws-northstar/layouts/Container";
import ImagePanel from "./ImagePanel";
import { LoadingIndicator } from "aws-northstar";

import { fetchImage } from "../utils/s3utils";


const ImageModal = ({ s3, s3url }) => {
  const [visible, setVisible] = useState(false);
  const [img, setImg] = useState("empty");

  const showImage = async (s3, s3url) => {
    setVisible(true)
    if (s3 !== (undefined || null)) {
      const s3Key = s3url.split("/")[1];
      try {
        const imageData = await fetchImage(s3, s3Key);
        const imgBlob = new Blob([imageData.buffer], { type: "image/webp" });
        setImg(imgBlob);  
      } catch (error) {
        alert('Cannot download image from S3!!!')
      }
    }
  };

  return (
    <>
      <Modal title="Image" visible={visible} onClose={() => setVisible(false)}>
        <Container>
          {img === "empty" ? (
            <LoadingIndicator label="loading" size="large" />
          ) : (
            <ImagePanel blob={img} />
          )}
        </Container>
      </Modal>
      <Button onClick={() => showImage(s3, s3url)}>Show Image</Button>
    </>
  );
};

export default ImageModal;
