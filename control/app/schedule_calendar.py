# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
"""Numeric UTC cron calendar; every helper shares this contract."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re

BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))


@dataclass(frozen=True)
class Cron:
    expression: str
    fields: tuple
    day_unrestricted: bool
    weekday_unrestricted: bool

    def matches(self, slot):
        date = datetime.fromtimestamp(slot, timezone.utc)
        minute, hour, day, month, weekday = self.fields
        if date.minute not in minute or date.hour not in hour or date.month not in month:
            return False
        dom = date.day in day
        dow = (date.weekday() + 1) % 7 in weekday
        return (dom and dow if self.day_unrestricted or self.weekday_unrestricted else dom or dow)


def compile_cron(expression):
    if not isinstance(expression, str) or len(expression) > 256:
        raise ValueError('Cron attendu : cinq champs numériques.')
    parts = expression.split()
    if len(parts) != 5:
        raise ValueError('Cron attendu : cinq champs numériques.')
    fields = []
    for part, (low, high) in zip(parts, BOUNDS):
        values = set()
        for item in part.split(','):
            match = re.fullmatch(r'(\*|[0-9]+(?:-[0-9]+)?)(?:/([0-9]+))?', item)
            if not match:
                raise ValueError('Champ cron invalide.')
            base, raw_step = match.groups()
            step = int(raw_step) if raw_step else 1
            if not 1 <= step <= high - low + 1:
                raise ValueError('Pas cron hors limites.')
            if base == '*':
                start, end = low, high
            else:
                ends = [int(value) for value in base.split('-')]
                start = ends[0]
                end = ends[-1] if len(ends) == 2 else high if raw_step else start
                if not low <= start <= end <= high:
                    raise ValueError('Plage cron invalide.')
            values.update(range(start, end + 1, step))
        fields.append(frozenset(value % 7 for value in values) if low == 0 and high == 7 else frozenset(values))
    return Cron(' '.join(parts), tuple(fields), parts[2] == '*', parts[4] == '*')


def boundary(timestamp):
    return int(timestamp // 300) * 300


def window_slots(cron, window, activated_at, retired_at=None):
    """At most five nominal UTC minute slots; activation is exclusive."""
    return [slot for slot in range(window - 240, window + 1, 60)
            if slot > activated_at and (retired_at is None or slot <= retired_at) and cron.matches(slot)]


def next_slot(cron, after):
    """Bounded Gregorian search, including the next leap day after a century."""
    # Day iteration avoids millions of minute probes for sparse expressions.
    date = datetime.fromtimestamp(after, timezone.utc)
    midnight = int(date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    for day_offset in range(8 * 366):
        start = midnight + day_offset * 86400
        current = datetime.fromtimestamp(start, timezone.utc)
        if current.month not in cron.fields[3]:
            continue
        for hour in sorted(cron.fields[1]):
            for minute in sorted(cron.fields[0]):
                slot = start + hour * 3600 + minute * 60
                if slot > after and cron.matches(slot):
                    return {'nominal_at': slot, 'window_at': boundary(slot + 299)}
    return None
