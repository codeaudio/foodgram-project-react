import base64
import random
import string
from io import BytesIO

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.template.loader import get_template


class Converter:
    @staticmethod
    def get_file_from_base64(serialize_file):
        format, imgstr = serialize_file.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(
            base64.b64decode(imgstr),
            name='temp.' + imgstr[:15] +
                 ''.join(random.choices(string.ascii_lowercase, k=15)) +
                 '.' + ext
        )


def render_to_pdf(template_src, context_dict=None):
    from xhtml2pdf import pisa

    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
