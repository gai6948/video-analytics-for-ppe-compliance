package com.example.videomonitoring.kvsframeparser;

import java.io.IOException;
import java.io.InputStream;
import java.util.Optional;

import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.DefaultAWSCredentialsProviderChain;
import com.amazonaws.kinesisvideo.parser.examples.ContinuousGetMediaWorker;
import com.amazonaws.kinesisvideo.parser.mkv.MkvElementVisitException;
import com.amazonaws.kinesisvideo.parser.utilities.FragmentMetadataVisitor;
import com.amazonaws.kinesisvideo.parser.utilities.FrameVisitor;
import com.amazonaws.kinesisvideo.parser.utilities.consumer.FragmentMetadataCallback;
import com.amazonaws.kinesisvideo.parser.utilities.consumer.GetMediaResponseStreamConsumer;
import com.amazonaws.kinesisvideo.parser.utilities.consumer.GetMediaResponseStreamConsumerFactory;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.kinesisvideo.AmazonKinesisVideo;
import com.amazonaws.services.kinesisvideo.AmazonKinesisVideoClientBuilder;
import com.amazonaws.services.kinesisvideo.model.StartSelector;
import com.amazonaws.services.kinesisvideo.model.StartSelectorType;

import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3AsyncClient;


public class KvsConsumer {
    public static void main(String[] args) {
        final String videoStreamName = System.getenv("CAMERA_NAME");
        final String bucketName = System.getenv("S3_BUCKET_NAME");
        final String region = System.getenv("AWS_DEFAULT_REGION");
        final int processFPS = Integer.valueOf(System.getenv("PROCESS_RATE_IN_FPS")).intValue();
        
        final AWSCredentialsProvider credentialsProvider = new DefaultAWSCredentialsProviderChain();
        final AmazonKinesisVideo amazonKinesisVideo = AmazonKinesisVideoClientBuilder.standard().withRegion(region)
                .build();

        final S3AsyncClient s3Client = S3AsyncClient.builder().region(Region.of(region)).build();

        GetMediaResponseStreamConsumerFactory consumerFactory = new GetMediaResponseStreamConsumerFactory() {
            @Override
            public GetMediaResponseStreamConsumer createConsumer() throws IOException {
                return new GetMediaResponseStreamConsumer() {
                    @Override
                    public void process(InputStream inputStream, FragmentMetadataCallback callback)
                            throws MkvElementVisitException, IOException {
                        processWithFragmentEndCallbacks(inputStream, callback,
                                FrameVisitor.create(
                                        new KvsS3Processor(s3Client, videoStreamName, 
                                                bucketName, processFPS),
                                        Optional.of(new FragmentMetadataVisitor.BasicMkvTagProcessor())));
                    }
                };
            }
        };

        ContinuousGetMediaWorker getMediaWorker = ContinuousGetMediaWorker.create(Regions.fromName(region),
                credentialsProvider, videoStreamName, new StartSelector().withStartSelectorType(StartSelectorType.NOW),
                amazonKinesisVideo, consumerFactory);

        // Long running task
        getMediaWorker.run();
    }
}
