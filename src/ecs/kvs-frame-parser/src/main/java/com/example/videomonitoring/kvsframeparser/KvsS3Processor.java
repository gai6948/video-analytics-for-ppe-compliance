package com.example.videomonitoring.kvsframeparser;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import javax.imageio.ImageIO;
import java.io.ByteArrayOutputStream;
import java.awt.image.BufferedImage;
import java.io.IOException;
import com.amazonaws.kinesisvideo.parser.mkv.Frame;
import com.amazonaws.kinesisvideo.parser.mkv.FrameProcessException;
import com.amazonaws.kinesisvideo.parser.utilities.FragmentMetadata;
import com.amazonaws.kinesisvideo.parser.utilities.H264FrameDecoder;
import com.amazonaws.kinesisvideo.parser.utilities.MkvTrackMetadata;
import com.amazonaws.kinesisvideo.parser.utilities.FragmentMetadataVisitor.MkvTagProcessor;
import software.amazon.awssdk.core.async.AsyncRequestBody;
import software.amazon.awssdk.services.s3.S3AsyncClient;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectResponse;

/**
 * A class provided to the KVS Parser Library that captures the frame and its
 * producer timestamp, and upload them to S3
 * 
 * @param s3Client The S3 Async Client
 */
public class KvsS3Processor extends H264FrameDecoder {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(KvsS3Processor.class);
    final S3AsyncClient s3Client;
    final String videoStreamName;
    final String bucketName;
    final int processFPS;
    static long lastProcessedFrameTimeStamp = 0;

    public KvsS3Processor(S3AsyncClient s3Client, String videoStreamName, String bucketName, int processFPS) {
        this.s3Client = s3Client;
        this.videoStreamName = videoStreamName;
        this.bucketName = bucketName;
        this.processFPS = processFPS;
    }

    @Override
    public void process(Frame frame, MkvTrackMetadata trackMetadata, Optional<FragmentMetadata> fragmentMetadata,
            Optional<MkvTagProcessor> tagProcessor) throws FrameProcessException {

        // Calculating timestamp of the frame
        int frameTimeDelta = frame.getTimeCode();
        long fragmentStartTime = fragmentMetadata.get().getProducerSideTimestampMillis();
        long frameTimeStamp = fragmentStartTime + frameTimeDelta;

        // Process frame at specified fps, ignore frame that is 1000/fps ms from latest
        // processed timestamp
        if (frameTimeStamp > lastProcessedFrameTimeStamp + 1000 / processFPS) {
            lastProcessedFrameTimeStamp = frameTimeStamp;

            // Obtain size of the frame
            int frameWidth = trackMetadata.getPixelWidth().get().intValue();
            int frameHeight = trackMetadata.getPixelHeight().get().intValue();

            // Decode frame with H264 codecs
            final BufferedImage bufferedImage = decodeH264Frame(frame, trackMetadata);
            try {
                byte[] frameData = toByteArray(bufferedImage);
                // Upload frame to S3
                uploadFrame(frameData, frameTimeStamp, frameWidth, frameHeight);
            } catch (Exception e) {
                System.out.println("Exception: " + e);
            }

        }
    }

    private byte[] toByteArray(BufferedImage img) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(img, "png", baos);
        byte[] bytes = baos.toByteArray();
        return bytes;
    }

    private void uploadFrame(byte[] frameData, long frameTimeStamp, int frameWidth, int frameHeight) {
        // Embed timestamp, frame dimension as metadata and upload frame to S3

        Date date = new Date(frameTimeStamp);
        SimpleDateFormat dateFormatter = new SimpleDateFormat("yyyy-MM-dd-hh-mm-ss-SSS");
        String timeStr = dateFormatter.format(date);
        String objKey = this.videoStreamName.concat("/").concat(timeStr).concat(".png");
        Map<String, String> objMetadata = new HashMap<String, String>();
        objMetadata.put("timestamp", String.valueOf(frameTimeStamp));
        objMetadata.put("frame-height", String.valueOf(frameHeight));
        objMetadata.put("frame-width", String.valueOf(frameWidth));

        PutObjectRequest s3PutRequest = PutObjectRequest.builder().bucket(this.bucketName).key(objKey)
                .metadata(objMetadata).build();
        
        CompletableFuture<PutObjectResponse> putObjectFuture = this.s3Client.putObject(s3PutRequest, AsyncRequestBody.fromBytes(frameData));

        putObjectFuture.whenComplete((resp, err) -> {
            try {
                if (resp != null) {
                    log.info("Frame uploaded");
                } else {
                    err.printStackTrace();
                }
            } catch (Exception e) {
                log.error(e.getMessage());
            }
        });

    }

    @Override
    public void close() {
        this.s3Client.close();
    }

}
