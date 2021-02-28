import os

from main.image_ops.converter import convert_frame

old_file = '/tmp/test-laptop-01-2021-01-27-10:54:50:532000.webp'

def test_convert_frame():
    new_file = convert_frame(old_file, '.png')
    assert new_file.endswith('.png')
