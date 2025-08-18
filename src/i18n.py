import json


__translations = {}


def set_locale(locale: str) -> None:
    global __translations
    with open(locale, "r") as file:
        __translations = json.load(file)


# TODO bug, for some reason this is not loaded at the start
set_locale("./assets/locales/en.json")


def __apply_locale_template(string: str, **kwargs) -> str:
    for kwarg in kwargs:
        key = "{{" + kwarg + "}}"
        string = string.replace(key, kwargs.get(kwarg))
    return string


def __get_translation_raw(key: str) -> any:
    keys = key.split(".")
    current = __translations
    for subkey in keys:
        if isinstance(current, dict):
            if subkey not in current:
                return None
            current = current[subkey]
        elif isinstance(current, list):
            # Key has to be a number, e.g. 'key.entries.0.value'
            if not subkey.isnumeric():
                return None
            subkey = int(subkey)
            if subkey < 0 or subkey >= len(current):
                return None
            current = current[int(subkey)]

    return current


def has(key) -> bool:
    return __get_translation_raw(key) is not None


def get(key: str, **kwargs) -> str | list[str] | None:
    translation = __get_translation_raw(key)

    if translation is None:
        return None
    elif isinstance(translation, str):
        translation = __apply_locale_template(translation, **kwargs)
    elif isinstance(translation, list):
        translation = [__apply_locale_template(e, **kwargs) for e in translation]
    else:
        return None

    return translation


def t(key: str, x: any = None, **kwargs) -> str | list[str] | None:
    t = get(key, **kwargs)
    return t.format(x=x) if x else t
