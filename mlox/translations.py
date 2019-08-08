
import locale
import codecs
from mlox.resources import resource_manager

# Utility functions
Lang = locale.getdefaultlocale()[0]
Lang = "en" if Lang == None or len(Lang) < 2 else Lang[0:2]
Encoding = locale.getpreferredencoding()

class dyndict(dict):
    """if item is in dict, return value, otherwise return item. for soft failure when looking up translations."""
    def __getitem__(self, item):
        return(super(dyndict, self).__getitem__(item) if item in self else item)


def load_translations(lang):
    """double-de-bungify the translation dictionary."""
    def splitter(x):
        s = x.split("]]")
        (key, val) = (s[0] if len(s) > 0 else "", s[1] if len(s) > 1 else "")
        trans = dict(list(map(lambda y: y.split('`'), val.split("\n`")))[1:])
        return(key, trans[lang].rstrip() if lang in trans else key)

    translations: bytes = resource_manager.resource_string("mlox.static", "mlox.msg")
    return dyndict(list(map(splitter, translations.decode("utf-8").split("\n[[")))[1:])


_ = load_translations(Lang)


def dump_translations(languages):
    """Dump the entire translation dictionary to stdout"""
    print("Languages translations for: %s" % languages[0])
    for key, value in (load_translations(languages[0]).items()):
        print("%s:" % key)
        print(" -> %s" % value.encode("utf-8"))
