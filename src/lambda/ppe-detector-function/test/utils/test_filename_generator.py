from datetime import datetime
from main.utils.filename_generator import generate_filename


def test_generate_filename():
    test_time = '1610094473985'
    camera_name = 'test-laptop-1'
    filename = generate_filename(test_time, camera_name)
    print(filename)
    assert filename == 'test-laptop-1-2021-01-08-08:27:53:985000.jpg'
