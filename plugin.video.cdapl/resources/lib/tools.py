# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

# Author: rysson
# License: MIT

import sys
import re

PY2 = sys.version_info < (3,)
PY3 = sys.version_info >= (3,)

if PY3:
    from urllib import parse as urlparse
    basestring = str
else:
    import urlparse


#: Regex type
regex = type(re.search('', ''))


#: Regex for clean BB-style.
re_clean = re.compile(r'^\s+|\[[^]]*\]|\s+$')
#: Regex for normalize string (single space).
re_norm = re.compile(r'\s+')


if PY3:
    def U(string):
        """Get unicode string."""
        if isinstance(string, str):
            return string
        if isinstance(string, bytes):
            return string.decode('utf-8')
        return str(string)
else:
    def U(string):
        """Get unicode string."""
        if isinstance(string, unicode):
            return string
        if isinstance(string, str):
            return string.decode('utf-8')
        return unicode(string)


def uclean(s):
    """Return clean unicode string. Remove [code...], normalize spaces, strip."""
    return re_norm.sub(' ', re_clean.sub('', U(s)))


def NN(n, word, *forms):
    """
    Translation Rules for Plurals for Polish language.
    See: https://doc.qt.io/qt-5/i18n-plural-rules.html
    >>> NN(number, 'pies', 'psy', 'psów')
    """
    forms = (word,) + forms + (word, word)
    if n == 1:
        return forms[0]
    if n % 10 >= 2 and n % 10 <= 4 and (n % 100 < 10 or n % 100 > 20):
        return forms[1]
    return forms[2]


def find_re(pattern, text, default='', flags=0, many=True):
    """
    Search regex pattern, return sub-expr(s) or whole found text or default.

    Pattern can be text (str or unicode) or compiled regex.

    When no sub-expr defined returns whole matched text (whole pattern).
    When one sub-expr defined returns sub-expr.
    When many sub-exprs defined returns all sub-exprs if `many` is True else first sub-expr.

    Ofcourse unnamed sub-expr (?:...) doesn't matter.
    """
    if not isinstance(pattern, regex):
        pattern = re.compile(pattern, flags)
    rx = pattern.search(text)
    if not rx:
        return default
    groups = rx.groups()
    if not groups:
        rx.group(0)
    if len(groups) == 1 or not many:
        return groups[0]
    return groups


def fragdict(url):
    """Returns URL fragment variables. URL can be str or urlparse.ParseResult()."""
    if isinstance(url, basestring):
        url = urlparse.urlparse(url or '')
    return dict(urlparse.parse_qsl(url.fragment))
