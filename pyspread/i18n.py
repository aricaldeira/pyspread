# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

'''

**Provides**

 * :class:`Settings`

'''

import os

import gettext

LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')

# set initial default language, based on OS-locale
# FIXME some module-level strings might get translated using this language, before
#       any user-provided custom language (in config) can get set.
language = gettext.translation('pyspread', LOCALE_DIR, fallback=True)
try:
    _lang = language.info().get('language', None)
except Exception as e:
    print(f'gettext setting initial language to ?? (error: {e!r})')
else:
    print(f'gettext setting initial language to {_lang!r}')


# note: do not use old-style (%) formatting inside translations,
#       as syntactically incorrectly translated strings would raise exceptions (see #3237).
#       e.g. consider  _('Connected to %d nodes.') % n
#                      >>> 'Connecté aux noeuds' % n
#                      TypeError: not all arguments converted during string formatting
# note: f-strings cannot be translated! see https://stackoverflow.com/q/49797658
#       So this does not work:   _(f'My name: {name}')
#       instead use .format:     _('My name: {}').format(name)
def _(message: str, *, context=None) -> str:
    if message == '':
        return ''  # empty string must not be translated. see #7158
    global language
    if context:
        contexts = [context]
        if context[-1] != '|':  # try with both '|' suffix and without
            contexts.append(context + '|')
        else:
            contexts.append(context[:-1])
        for ctx in contexts:
            out = language.pgettext(ctx, message)
            if out != message:  # found non-trivial translation
                return out
        # else try without context
    return language.gettext(message)


def set_language(lang: str = None) -> None:
    global language

    if not lang:
        import locale as system_locale

        lang = system_locale.getlocale()[0]

        if lang == 'C' or (not lang):
            lang = ''

        lang = lang.replace('-', '_')

        if '.' in lang:
            lang = lang.split('.')[0]

    print(f'Setting language to {lang}')
    language = gettext.translation('pyspread', LOCALE_DIR, fallback=True, languages=[lang])


languages = {
    '': _('Default'),
    'bz_BR': _('Brazilian'),
    'en_GB': _('English'),
    'pt_BR': _('Brazilian Portuguese'),
    'pt_PT': _('European Portuguese'),
}
assert '' in languages
