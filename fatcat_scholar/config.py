from dynaconf import Dynaconf


settings = Dynaconf(settings_file="settings.toml", environments=True,)
