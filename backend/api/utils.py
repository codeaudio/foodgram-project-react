import base64
import random
import string

from django.core.files.base import ContentFile


def get_file_from_base64(serialize_file):
    format, imgstr = serialize_file.split(';base64,')
    ext = format.split('/')[-1]
    return ContentFile(
        base64.b64decode(imgstr),
        name='temp.' + imgstr[:15] + ''.join(random.choices(string.ascii_lowercase, k=15)) + '.' + ext
    )
