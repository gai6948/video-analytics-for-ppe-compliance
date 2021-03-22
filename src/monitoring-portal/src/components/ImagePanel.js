import Container from "aws-northstar/layouts/Container";

const ImagePanel = ({ blob }) => {
  console.log(blob);

  return (
    <Container>
      <img
        src={window.URL.createObjectURL(blob)}
        alt=""
        className='image-box'
        width='480'
        height='320'
      />
    </Container>
  );
};

export default ImagePanel;
