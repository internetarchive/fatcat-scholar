import subprocess
from dynaconf import Dynaconf

settings = Dynaconf(settings_file="settings.toml", environments=True,)

GIT_REVISION = subprocess.check_output(["git", "describe", "--always"]).strip().decode('utf-8')
