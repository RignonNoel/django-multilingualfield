from django import forms
import simplejson as json
from django.utils import six

from .widgets import MLTextWidget
from .language import LanguageText


class MLTextFormField(forms.CharField):

    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = MLTextWidget
        super(MLTextFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        """
        Try to get JSON format of the value
        :param value: The value we want to clean
        :return: The best format of value available
        """
        value = super(MLTextFormField, self).clean(value)
        if not value:
            return value
        if isinstance(value, six.string_types):
            try:
                valuejson = json.loads(value)
                Lang = LanguageText()
                Lang.values = valuejson
                return Lang
            except ValueError:
                try:
                    Lang = LanguageText(value, language=None)
                    return Lang
                except Exception:  # Look like there will be no error, is it good?
                    raise forms.ValidationError(
                        'JSON decode error: %s' % (unicode(exc),)
                    )
        else:
            return value
