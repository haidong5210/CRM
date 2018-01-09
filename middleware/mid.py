import re
from django.conf import settings
from django.shortcuts import redirect


class MiddlewareMixin(object):
    def __init__(self, get_response=None):
        self.get_response = get_response
        super(MiddlewareMixin, self).__init__()

    def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        if not response:
            response = self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response


class Md(MiddlewareMixin):
    def process_request(self,request):
        current_url = request.path
        for re_url in settings.WIGHT_ORDER:
            if re.match(re_url,current_url):
                return None
        if not request.session.get(settings.USERINFO):
            return redirect('/login/')