from django.conf import settings


def app_version(request):
    # return the value you want as a dictionnary.
    # you may add multiple values in there.
    return {"APP_VERSION": settings.VERSION}
