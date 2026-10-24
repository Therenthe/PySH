"""A small owner-control projection; never send preferences or network state to sites."""


def controls_snapshot(audio, power, presentation, busy=False):
    audio = audio if isinstance(audio, dict) else {}
    power = power if isinstance(power, dict) else {}
    brightness = power.get('brightness') if isinstance(power.get('brightness'), dict) else {}
    source = audio.get('outputs') if isinstance(audio.get('outputs'), list) else []
    outputs = []
    seen = set()
    for item in source[:32]:
        if not isinstance(item, dict):
            continue
        identifier = item.get('id')
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 200 or not identifier.isprintable() or identifier in seen:
            continue
        seen.add(identifier)
        label = item.get('description') or item.get('name') or identifier
        label = label if isinstance(label, str) else identifier
        outputs.append({'id': identifier, 'label': label[:300], 'active': item.get('active') is True or audio.get('output') == identifier})
    volume, level = audio.get('volume'), brightness.get('value')
    return {
        'language': presentation['language'], 'theme': presentation['theme'],
        'busy': bool(busy or power.get('standby')),
        'audio': {
            'available': audio.get('available') is True,
            'ready': audio.get('ready') is True,
            'volume': volume if type(volume) is int and 0 <= volume <= 100 else None,
            'mute': audio.get('mute') if type(audio.get('mute')) is bool else None,
            'outputs': outputs,
        },
        'brightness': {
            'available': brightness.get('available') is True,
            'value': level if type(level) is int and 1 <= level <= 100 else None,
        },
    }
