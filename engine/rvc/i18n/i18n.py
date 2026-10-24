import json
import locale
import os
from pathlib import Path
LOCALES = Path(__file__).resolve().parent / "locale"
from tools.file_io import read_text


def load_language_list(language):
    return json.loads(read_text(LOCALES / f"{language}.json"))


class I18nAuto:
    def __init__(self, language=None):
        if language in ["Auto", None]:
            language = locale.getdefaultlocale()[
                0
            ]  # getlocale can't identify the system's language ((None, None))
        if not os.path.exists(LOCALES / f"{language}.json"):
            language = "en_US"
        self.language = language
        self.language_map = load_language_list(language)

    def __call__(self, key):
        return self.language_map.get(key, key)

    def __repr__(self):
        return "Use Language: " + self.language
