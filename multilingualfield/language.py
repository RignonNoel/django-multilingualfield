from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models, DatabaseError, transaction
from django.utils.translation import ugettext_lazy as _, get_language

try:
    import json
except ImportError:
    import simplejson as json


def get_base_language(lang):
    """
    Get the base language of language code (ex: 'fr-ca' -> 'fr')
    :param lang: The language code
    :return: The base language of the language code
    """
    if '-' in lang:
        return lang.split('-')[0]
    return lang
    

def get_current_language(base=True):
    """
    Find the current language used by the platform
    :param base:
    :return: The current language used by the platform
    """
    language = get_language()
    if base:
        return get_base_language(language)
    return language
    

class LanguageText(object):
    """
    Store text with language code in JSON format
    """
    values = {}
    default_language = None
    max_length = -1
    
    def __init__(self, value=None, language=None, default_language=None, max_length=-1):
        self.max_length = max_length
        self.default_language = default_language
        self.values = {}
        if value is not None:
            self.value(value, language)
            
    def __call__(self, value=None, language=None):
        self.value(value, language)
        return self
            
    def get_available_language(self):
        """
        Get available languages in the JSON content
        :return: A list of language code
        """
        return self.values.keys()

    def get_current_language(self, base=False):
        """
        Find the current language used by the platform
        :param base:
        :return: The current language used by the platform
        """
        return get_current_language(base)
    
    def remove_language(self, lang):
        """
        Remove a language from the list of language available in the JSON
        :param lang: The language code we want to remove
        :return: The value we removed from the JSON
        """
        try:
            return self.values.pop(lang)
        except Exception:
            pass
    
    def has_language(self, language):
        """
        Find if a specific language is available in the JSON
        :param language: The language code we want
        :return: True if the language is available
        """
        return language in self.values
            
    def get(self, language=None, fallback=True):
        """
        Get the value of the language we want
        :param language: A language code
        :param fallback: If True, we return a translation if this one is not available
        :return: A translation available in the JSON
        """
        # We find we language we want to get
        if language is None:
            language = get_current_language(False)
        else:
            language = language

        # We find the current language used by the platform
        curr_lang_base = get_current_language(True)

        # We return the value
        if language in self.values:
            return self.values[language]
        if not fallback:
            return None
        if curr_lang_base in self.values:
            return self.values[curr_lang_base]
        if self.default_language in self.values:
            return self.values[self.default_language]
        try:
            first_lang = self.values.keys()[0]
            return self.values[first_lang]
        except Exception:
            pass
        return None
    
    def value(self, value=None, language=None):
        """
        Accessor of the internationalized value
        :param value: If not `None` it's the value you want to set
        :param language: The language you want to set or get
        :return: The translation if value is defined, `None` otherwise
        """
        if value is None:
            # Get value
            return self.get(language)
        else:
            # Set value
            if language is None:
                language = get_current_language(False)
            if self.max_length != -1:
                value = value[:self.max_length]
            self.values[language] = value
            return None
        
    def __unicode__(self):
        return self.value()
        
    def __str__(self):
        return unicode(self.value()).encode('utf-8')
    
    def __repr__(self):
        return unicode(self.value()).encode('utf-8')
