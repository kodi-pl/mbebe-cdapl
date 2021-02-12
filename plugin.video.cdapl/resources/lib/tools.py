# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

# Author: rysson
# License: MIT

import re
import urlparse


#: Regex type
regex = type(re.search('', ''))


#: Regex for clean BB-style.
re_clean = re.compile(ur'^\s+|\[[^]]*\]|\s+$')
#: Regex for normalize string (single space).
re_norm = re.compile(ur'\s+')


def U(string):
    """Get unicode string."""
    if isinstance(string, unicode):
        return string
    if isinstance(string, str):
        return string.decode('utf-8')
    return unicode(string)


def uclean(s):
    """Return clean unicode string. Remove [code...], normalize spaces, strip."""
    return re_norm.sub(u' ', re_clean.sub(u'', U(s)))


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


def find_re(pattern, text, default='', flags=0):
    """Search regex pattern, return first sub-expr or whole found text or default."""
    if not isinstance(pattern, regex):
        pattern = re.compile(pattern, flags)
    rx = pattern.search(text)
    return rx.group(1 if rx.groups() else 0) if rx else default


def fragdict(url):
    """Returns URL fragment variables. URL can be str or urlparse.ParseResult()."""
    if isinstance(url, basestring):
        url = urlparse.urlparse(url or '')
    return dict(urlparse.parse_qsl(url.fragment))
