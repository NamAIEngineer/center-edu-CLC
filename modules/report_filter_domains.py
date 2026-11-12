"""Runtime domains for observed calendar filters; inventories remain historical."""
from datetime import date
import re


def current_year_filters(filters, *, today=None):
    today = today or date.today()
    result = []
    for raw in filters:
        item = dict(raw)
        options = item.get('options') or ()
        if item.get('name') in {'year', 'select_year'} and options and all(re.fullmatch(r'(?:Năm\s+)?\d{4}', str(value)) for value in options):
            first = min(int(re.search(r'\d{4}', str(value)).group()) for value in options)
            prefix = 'Năm ' if str(options[0]).startswith('Năm ') else ''
            item['options'] = tuple(f'{prefix}{year}' for year in range(first, today.year + 6))
            item['default'] = f'{prefix}{today.year}'
        result.append(item)
    return tuple(result)
