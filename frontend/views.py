from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.html import strip_tags
from django.http import HttpResponse, Http404, HttpResponseRedirect
from settings import APP_NAME
import sys, logging
from fbook.views import REDIRECT_LINK

logger = logging.getLogger()

def index(request):
    return render_to_response('frontend/index.html',{ 'REDIRECT_LINK':REDIRECT_LINK, 'APP_NAME':APP_NAME })
