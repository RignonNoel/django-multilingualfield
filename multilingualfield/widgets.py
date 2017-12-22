from django.forms import Textarea
from django import forms
import simplejson as json
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import six, translation
from multilingualfield import settings as ml_settings

from .language import LanguageText

DEFAULT_CKCONFIG = dict()


class MLTextWidget(Textarea):
    """
    Widget used to display a multi-language field
    """
    HTML = False

    def __init__(self, html=False, textarea=False, *args, **kwargs):
        self.HTML = html
        self.textarea = textarea

        super(MLTextWidget, self).__init__(*args, **kwargs)

    @property
    def media(self):
        """
        Define all media needed by the widget to be operational
        :return: a forms.Media instance with all CSS and JS script needed
        """
        # Javascript
        js = [
            'multiligualfield/js/jquery-1.10.2.min.js',
            'multiligualfield/js/jquery-ui-1.10.3.custom.min.js',
            'multiligualfield/js/json.js'
        ]
        if self.HTML:
            js += ['multiligualfield/ckeditor/ckeditor.js']

        # Cascading Style Sheets
        css = ['multiligualfield/css/ui-darkness/jquery-ui-1.10.3.custom.min.css']

        return forms.Media(js=js, css={'all': css})

    def render(self, name, value, attrs=None):
        """
        Render the template widget
        :param name: The name of the field we want to display
        :param value: The actual value of the field we want to display
        :param attrs:
        :return: A template of widget initialized
        """

        print(value)
        print(type(value))
        is_valid = False
        if value is None or value == '':
            # New create or edit none
            ml_json = '{}'
            ml_language = '[]'
            is_valid = True
        if isinstance(value, LanguageText):
            ml_json = json.dumps(value.values)
            ml_language = json.dumps(value.get_available_language())
            is_valid = True
        if isinstance(value, six.string_types):  # Debug :(
            print "Why string here ==================="
            print value
            print "===============================Why?"
        if is_valid:
            Langs = json.dumps(dict(settings.LANGUAGES))
            if self.HTML:
                widget_template = "multilingualfield/MLHTMLWidget.html"
            if self.textarea:
                widget_template = "multilingualfield/MLTextareaWidget.html"
            else:
                widget_template = "multilingualfield/MLTextWidget.html"
            return mark_safe(render_to_string(
                widget_template,
                {
                    "id": id(self),
                    "name": name,
                    "raw": value,
                    "ml_json": ml_json,  # Content JSON
                    "ml_language": ml_language,  # Available languages
                    "langs": Langs,
                    "langsobj": settings.LANGUAGES,
                    'current_language': translation.get_language(),
                    'CKEDITOR_FILER': ml_settings.CKEDITOR_FILER,
                    'CKEDITOR_BROWSER_URL': ml_settings.CKEDITOR_BROWSER_URL
                }
            ))

        return "Invalid data '%s'" % value
