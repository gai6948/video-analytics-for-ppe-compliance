from datetime import datetime


def generate_filename(timestamp: str, camera_name: str) -> str:
    """
    Generate filename 
    :param `timestamp` timestamp of the frame
    :param `camera_name` height of the frame, obtained from Kinesis payload
    """
    timestamp_in_sec = int(timestamp)/1000
    transformed_date = str(datetime.utcfromtimestamp(timestamp_in_sec)).replace(' ', '-').replace('.', ':')
    return camera_name + '-' + transformed_date + '.webp'
