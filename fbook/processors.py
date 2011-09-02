from wootmatch import settings
def app_name(request):
    return {'app_name': settings.APP_NAME}
