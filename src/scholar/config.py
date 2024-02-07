import subprocess

from dynaconf import Dynaconf

settings = Dynaconf(
    settings_file="settings.toml",
    environments=True,
)

GIT_REVISION = (
    subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
)

I18N_LANG_OPTIONS = [
    "ar",
    "de",
    "el",
    "es",
    "en",
    "fa",
    "fr",
    "hr",
    "it",
    "ko",
    "nb",
    "nl",
    "pt",
    "ru",
    "zh",
]
assert settings.I18N_LANG_DEFAULT in I18N_LANG_OPTIONS
