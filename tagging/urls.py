"""
urls for tagging app
"""
from django.conf.urls import patterns, url

from tagging.views import AjaxTagsListView

urlpatterns = patterns('tagging.views',
                       url(r'^tags_list$', AjaxTagsListView.as_view(),
                           name='get_tagging_list'),)
