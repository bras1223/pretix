#
# Caught customization: register additional shop/PDF fonts.
#
from django.dispatch import receiver

from pretix.presale.style import register_fonts

BASE = 'fonts/cabin'


@receiver(register_fonts, dispatch_uid='caught_cabin_font')
def register_cabin_font(sender, **kwargs):
    """Cabin (SIL Open Font License 1.1) — Impallari Type / The Cabin Project Authors."""
    return {
        'Cabin': {
            'regular': {
                'truetype': f'{BASE}/Cabin-Regular.ttf',
                'woff': f'{BASE}/Cabin-Regular.woff',
                'woff2': f'{BASE}/Cabin-Regular.woff2',
            },
            'bold': {
                'truetype': f'{BASE}/Cabin-Bold.ttf',
                'woff': f'{BASE}/Cabin-Bold.woff',
                'woff2': f'{BASE}/Cabin-Bold.woff2',
            },
            'italic': {
                'truetype': f'{BASE}/Cabin-Italic.ttf',
                'woff': f'{BASE}/Cabin-Italic.woff',
                'woff2': f'{BASE}/Cabin-Italic.woff2',
            },
            'bolditalic': {
                'truetype': f'{BASE}/Cabin-BoldItalic.ttf',
                'woff': f'{BASE}/Cabin-BoldItalic.woff',
                'woff2': f'{BASE}/Cabin-BoldItalic.woff2',
            },
        },
    }
