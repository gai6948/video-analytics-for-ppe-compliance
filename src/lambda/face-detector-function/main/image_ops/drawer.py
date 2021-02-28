import timeit
import cv2
import numpy as np

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

color_mapping = {
    0: (153, 0, 0),
    1: (255, 51, 255),
    2: (102, 0, 51),
    3: (0, 153, 0),
    4: (0, 0, 204),
    5: (102, 102, 255),
    6: (64, 64, 64),
    7: (204, 204, 204),
    8: (153, 76, 0),
    9: (51, 255, 51),
    10: (35, 237, 252),
    11: (34, 33, 36),
    12: (245, 123, 16),
    13: (245, 16, 153),
    14: (153, 204, 255)
}

@tracer.capture_method(capture_response=False)
def draw_bounding_box(face_res: list, size_list: list, frame: np.ndarray, filepath: str):
    """
    Draw bounding box on the frame based on the detected faces' bounding box coordinates
    :param: `face_res` List containing the Rekognition face search
    :param: `size_list` List containing the size of each cropped frame, in same order as the face response
    :param: `frame` The original uncropped frame
    :param: The path to drawn frame
    """

    start_time = timeit.default_timer()

    ppl_count = 0

    for ppl in face_res:
        height, width = frame.shape[:2]
        # print(height)
        # print(width)
        cropped_frame_height = size_list[ppl_count][0]
        cropped_frame_width = size_list[ppl_count][1]
        # print(cropped_frame_height)
        # print(cropped_frame_width)
        label_left = face_res[ppl_count]["SearchedFaceBoundingBox"]["Left"] / cropped_frame_width * width
        label_top = face_res[ppl_count]["SearchedFaceBoundingBox"]["Top"] / cropped_frame_width * height
        if label_left > 0.0 and label_left < 1.0: # Ignore drawing if the bounding box is outside of frame
            if label_top > 0.0 and label_top < 1.0:
                label_height = face_res[ppl_count]["SearchedFaceBoundingBox"]["Height"] * cropped_frame_height / height
                label_width = face_res[ppl_count]["SearchedFaceBoundingBox"]["Width"] * cropped_frame_width / width
                x1 = int(label_left * width)
                y1 = int(label_top * height)
                x2 = int(x1 + label_width * width)
                y2 = int(y1 + label_height * height)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_mapping[ppl_count], 5)
                cv2.putText(frame, f'Face-ID: {face_res[ppl_count]["FaceMatches"][0]["Face"]["FaceId"]}', (int(x1 * 0.9) , y1 - 5), cv2.FONT_HERSHEY_COMPLEX, 0.3, color_mapping[14-ppl_count], 1)
            else:
                logger.info("Person out of bound, skip drawing")
        else:
            logger.info("Person out of bound, skip drawing")

        ppl_count += 1

    cv2.imwrite(filepath, frame)

    logger.info(
        f'Image drawing completed after: {timeit.default_timer() - start_time}')
