"""Frozen zero-shot utility answer handling; no condition-dependent cleanup."""
from decimal import Decimal, InvalidOperation
import re


def parse_gsm8k(reply):
    # Last marker is authoritative. A malformed final marker cannot fall back
    # to an earlier correct-looking number or an arbitrary number in the text.
    if '####' not in reply:
        return None
    last = reply.rsplit('####', 1)[1].strip()
    if not re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', last):
        return None
    try:
        return Decimal(last.replace(',', ''))
    except InvalidOperation:
        return None


def gsm8k_correct(reply, gold):
    value = parse_gsm8k(reply)
    return value is not None and value == Decimal(str(gold).replace(',', ''))


def arc_choice(candidate_logits, letters=('A', 'B', 'C', 'D')):
    assert len(candidate_logits) == len(letters)
    # Python max preserves the first canonical option on an exact tie.
    return letters[max(range(len(letters)), key=lambda i: candidate_logits[i])]


if __name__ == '__main__':
    assert parse_gsm8k('work\n#### 1,234.50') == Decimal('1234.5')
    assert parse_gsm8k('#### -2') == -2
    assert parse_gsm8k('#### 9\n#### invalid') is None
    assert parse_gsm8k('#### 1/2') is None
    assert parse_gsm8k('#### 1,23') is None
    assert parse_gsm8k('The answer is 7') is None
    assert not gsm8k_correct('missing', 7)
    assert gsm8k_correct('#### 4.0', 4)
    assert arc_choice([1, 1, 0, -1]) == 'A'
