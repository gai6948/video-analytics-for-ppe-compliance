import timeit
from typing import Tuple
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

# Extract frame data along with embedded metadata from the blob received from Kinesis
@tracer.capture_method(capture_response=False)
def extract_data(data: bytes) -> Tuple[str, int, int, bytes]:
    start_time = timeit.default_timer()
    
    # Extract timestamp (first 13 bytes in the blob)
    timestamp_bytes = data[0:13]

    # Decode the timestamp using UTF-8
    timestamp = timestamp_bytes.decode('utf8')

    # Extract frame width (next 4 byte in the blob)
    width_bytes = data[13:17]
    frame_width = int.from_bytes(width_bytes, byteorder='big')

    # Extract frame height (next 4 byte in the blob)
    height_bytes = data[17:21]
    frame_height = int.from_bytes(height_bytes, byteorder='big')

    # The rest is frame data
    raw_frame = data[21:]

    logger.info(f"Raw frame in the blob is of size {len(raw_frame)} bytes")
    logger.info(f'Extracted data from blob after: {timeit.default_timer() - start_time}')
    return timestamp, frame_width, frame_height, raw_frame
