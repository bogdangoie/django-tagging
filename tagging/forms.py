"""
Form components for tagging.
"""
from django import forms
from django.forms import widgets
from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from tagging import settings
from tagging.models import Tag
from tagging.utils import parse_tag_input


class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('name',)

    def clean_name(self):
        value = self.cleaned_data['name']
        tag_names = parse_tag_input(value)
        if len(tag_names) > 1:
            raise forms.ValidationError(_('Multiple tags were given.'))
        return value


class TagField(forms.CharField):
    """
    A ``CharField`` which validates that its input is a valid list of
    tag names.
    """
    def clean(self, value):
        value = super(TagField, self).clean(value)
        for tag_name in parse_tag_input(value):
            if len(tag_name) > settings.MAX_TAG_LENGTH:
                raise forms.ValidationError(
                    _('Each tag may be no more than %s characters long.') %
                    settings.MAX_TAG_LENGTH)
        return value


class TagWidgetSelect2(widgets.SelectMultiple):
    """
    Override of the standard Django HiddenInput to output the same field, but
    using slightly different
    HTML
    """

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.1/css/'
                    'select2.min.css',)
        }
        js = ('https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.1/js/'
              'select2.js',)

    def render(self, name, value, attrs=None, choices=()):
        if value:
            if isinstance(value, basestring):
                value = value.split(',')
            for val in value:
                choices += ((val, val),)
        attrs = attrs if attrs else {}
        attrs.update({
            'style': 'width:80%;',
            'type': 'hidden'
        })
        rendered = super(TagWidgetSelect2, self).render(name, value, attrs,
                                                        choices)
        rendered_template = get_template('tagging/tagging-select2.html').\
            render(Context({'name': name}))
        rendered += '\n<script type="text/javascript">\n'
        rendered += rendered_template
        rendered += '\n</script>\n'
        return mark_safe(rendered)


class TagFieldSelect2(forms.CharField):
    """
    A ``CharField`` which validates that its input is a valid list of
    tag names - Select2.
    """
    widget = TagWidgetSelect2

    def clean(self, value):
        # value is a list of multiple values
        value = ",".join(value)
        value = super(TagFieldSelect2, self).clean(value)
        for tag_name in parse_tag_input(value):
            if len(tag_name) > settings.MAX_TAG_LENGTH:
                raise forms.ValidationError(
                    _('Each tag may be no more than %s characters long.') %
                    settings.MAX_TAG_LENGTH)
        return value
