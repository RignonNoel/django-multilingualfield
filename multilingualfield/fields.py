from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models, DatabaseError, transaction
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils import six

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from .language import LanguageText
from .forms import MLTextFormField
from .widgets import MLTextWidget


def get_base_language(lang):
    """
    Get the base language of language code (ex: 'fr-ca' -> 'fr')
    :param lang: The language code
    :return: The base language of the language code
    """
    if '-' in lang:
        return lang.split('-')[0]
    return lang


def get_current_language():
    """
    Find the current language used by the platform
    :return: The current language used by the platform
    """
    language = get_language()
    return get_base_language(language)


class MLTextField(six.with_metaclass(models.SubfieldBase, models.Field)):
    """
    A field that support multilingual text for your model
    """

    __metaclass__ = models.SubfieldBase

    default_error_messages = {
        'invalid': _("'%s' is not a valid JSON string.")
    }

    description = "Multilingual Text Field"

    def __init__(self, *args, **kwargs):
        # Keep the default value and force default=None to respect DB limitation on text/BLOB
        self.default_value = kwargs.get('default')
        kwargs['default'] = None

        self.lt_max_length = kwargs.pop('max_length', -1)
        self.default_language = kwargs.get('default_language', get_current_language())
        super(MLTextField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Prepare the value to be store in database
        :param value: The value we want to store
        :return: `None` or a dumps of JSON
        """
        if value is None:
            if not self.null and self.blank:
                if self.default_value:
                    return self.default_value
                else:
                    return ""
            return None
        if isinstance(value, six.string_types):
            value = LanguageText(
                value,
                language=None,
                max_length=self.lt_max_length,
                default_language=self.default_language
            )
        if isinstance(value, LanguageText):
            value.max_length = self.lt_max_length
            value.default_language = self.default_language
            return json.dumps(value.values)
        return None

    def get_db_prep_value(self, value, connection=None, prepared=None):
        return self.get_prep_value(value)

    def validate(self, value, model_instance):
        """
        Validate the field value
        :param value: The value of the field
        :param model_instance:
        :return: Nothing, just raise some type of error
        """
        if not self.null and value is None:
            raise ValidationError(self.error_messages['null'])
        try:
            self.get_prep_value(value)
        except Exception:
            raise ValidationError(self.error_messages['invalid'] % value)

    def get_internal_type(self):
        """
        Get internal type
        :return: A string who represent the internal type
        """
        return 'TextField'

    def db_type(self, connection):
        """
        Get database type
        :param connection:
        :return: A string who represent the database type used to store the value
        """
        if self.lt_max_length > 0:
            return 'char(%s)' % self.lt_max_length
        else:
            return 'text'

    def to_python(self, value):
        if isinstance(value, six.string_types):
            if value == "" or value is None:
                if self.null:
                    return None
                if self.blank:
                    return LanguageText(
                        "",
                        language=None,
                        max_length=self.lt_max_length,
                        default_language=self.default_language
                    )  # a A blank LanguageText object
            try:
                valuejson = json.loads(value)
                Lang = LanguageText(
                    max_length=self.lt_max_length,
                    default_language=self.default_language
                )
                Lang.values = valuejson
                return Lang

            except ValueError:
                try:
                    Lang = LanguageText(
                        value,
                        language=None,
                        max_length=self.lt_max_length,
                        default_language=self.default_language
                    )
                    return Lang

                except Exception:
                    msg = self.error_messages['invalid'] % value
                    raise ValidationError(msg)

        if isinstance(value, LanguageText):
            return value
        return LanguageText(
            "",
            language=None,
            max_length=self.lt_max_length,
            default_language=self.default_language
        )  # a A blank LanguageText object

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type in ["exact", "iexact"]:
            return self.to_python(self.get_prep_value(value))
        if lookup_type == "in":
            return [self.to_python(self.get_prep_value(v)) for v in value]
        if lookup_type == "isnull":
            return value
        if lookup_type in ["contains", "icontains"]:
            if isinstance(value, (list, tuple)):
                raise TypeError("Lookup type %r not supported with argument of %s" % (
                    lookup_type, type(value).__name__
                ))
                # Need a way co combine the values with '%', but don't escape that.
                return self.get_prep_value(value)[1:-1].replace(', ', r'%')
            if isinstance(value, dict):
                return self.get_prep_value(value)[1:-1]
            return self.to_python(self.get_prep_value(value))
        raise TypeError('Lookup type %r not supported' % lookup_type)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': MLTextFormField,
        }

        if self.lt_max_length == -1:
            # If we don't have max_length, it's a textare
            defaults['widget'] = MLTextWidget(textarea=True)
        else:
            defaults['widget'] = MLTextWidget

        defaults.update(**kwargs)
        return super(MLTextField, self).formfield(**defaults)

    def value_to_string(self, obj):
        return self._get_val_from_obj(obj)


class MLHTMLField(MLTextField):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': MLTextFormField,
            'widget': MLTextWidget(HTML=True)
        }
        defaults.update(**kwargs)
        return super(MLHTMLField, self).formfield(**defaults)


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ['^multilingualfield\.fields\.MLTextField'])
    add_introspection_rules([], ['^multilingualfield\.fields\.MLHTMLField'])
except ImportError:
    pass
