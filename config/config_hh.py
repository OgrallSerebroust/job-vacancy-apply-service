from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .config_base import ConfigBase


class ConfigHh(ConfigBase):
    model_config = SettingsConfigDict(
        env_prefix="HH_",
    )
    main_url: str = Field(
        frozen=True,
    )
    resume_id: str = Field(
        frozen=True,
    )  # TODO When we add resume choice, don't forget to make it SecretStr
    resume_vacancies_url: str = Field(
        frozen=True,
    )
    vacancy_url: str = Field(
        frozen=True,
    )
