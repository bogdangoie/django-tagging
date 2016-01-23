"""
Tagging related views.
"""
from django.http import Http404
from django.views.generic import View
from django.views.generic.list import ListView
from django.utils.translation import ugettext as _
from django.core.exceptions import ImproperlyConfigured

from base.utils.json_view import JSONViewMixin
from tagging.models import Tag
from tagging.models import TaggedItem
from tagging.utils import get_tag
from tagging.utils import get_queryset_and_model


class TaggedObjectList(ListView):
    """
    A thin wrapper around
    ``django.views.generic.list.ListView`` which creates a
    ``QuerySet`` containing instances of the given queryset or model
    tagged with the given tag.

    In addition to the context variables set up by ``object_list``, a
    ``tag`` context variable will contain the ``Tag`` instance for the
    tag.

    If ``related_tags`` is ``True``, a ``related_tags`` context variable
    will contain tags related to the given tag for the given model.
    Additionally, if ``related_tag_counts`` is ``True``, each related
    tag will have a ``count`` attribute indicating the number of items
    which have it in addition to the given tag.
    """
    tag = None
    related_tags = False
    related_tag_counts = True

    def get_tag(self):
        if self.tag is None:
            try:
                self.tag = self.kwargs.pop('tag')
            except KeyError:
                raise AttributeError(
                    _('TaggedObjectList must be called with a tag.'))

        tag_instance = get_tag(self.tag)
        if tag_instance is None:
            raise Http404(_('No Tag found matching "%s".') % self.tag)

        return tag_instance

    def get_queryset_or_model(self):
        if self.queryset is not None:
            return self.queryset
        elif self.model is not None:
            return self.model
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset_or_model()." % {
                    'cls': self.__class__.__name__
                }
            )

    def get_queryset(self):
        self.queryset_or_model = self.get_queryset_or_model()
        self.tag_instance = self.get_tag()
        return TaggedItem.objects.get_by_model(
            self.queryset_or_model, self.tag_instance)

    def get_context_data(self, **kwargs):
        context = super(TaggedObjectList, self).get_context_data(**kwargs)
        context['tag'] = self.tag_instance

        if self.related_tags:
            queryset, model = get_queryset_and_model(self.queryset_or_model)
            context['related_tags'] = Tag.objects.related_for_model(
                self.tag_instance, model, counts=self.related_tag_counts)
        return context


class AjaxTagsListView(View, JSONViewMixin):
    """
    Ajax View that retrieves a list of tags that match a certain query
    """

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404

        def param(param_name, is_int=False):
            try:
                return int(request.GET[param_name]) if is_int else \
                    request.GET[param_name]
            except Exception:
                return None
        query = param('query')
        limit = param('limit', True) or 10
        tags = []

        if query:
            kwargs.update({'name__contains': query})
            tags = list(Tag.objects.filter(**kwargs).values_list(
                    'name', flat=True)[:limit])
        response = {'tags': tags}
        # return the response
        return self.json_response(dict(response))
