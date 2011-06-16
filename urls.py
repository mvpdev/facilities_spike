from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from facilities.urls import urlpatterns
#urlpatterns = patterns('',
#    url(r'^$', include('facilities_spike.facilities.urls')),
#)
