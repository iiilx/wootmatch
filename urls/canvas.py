from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^fandjango/', include('fandjango.urls')),
)

urlpatterns += patterns('wootmatch.fbook.views',
    url(r'^$', 'canvas', name='canvas'),
    url(r'^remove-person$', 'remove_person', name='remove_person'),
    #url(r'^remove$', 'remove', name='remove'),
    #url(r'^update-matches$', 'update_matches', name='update_matches'),
    url(r'^change-email$', 'change_email', name='change_email'),
    url(r'^add-person$', 'add_person', name='add_person'),
    url(r'^update-rank$', 'update_rank', name='update_rank'),
    url(r'^deauthorize', 'deauthorize_application'),
    url(r'^accounts/delete','delete_account', name="delete_account"),
    url(r'^request-features', 'request_features',name='request_features'),    
    url(r'^upvote', 'upvote', name='upvote'),
    url(r'^create-msg', 'create_msg', name='create_msg'),
    url(r'^get-msg', 'get_msg', name='get_msg'),
    url(r'test','test'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^sentry/', include('sentry.web.urls')),
)
