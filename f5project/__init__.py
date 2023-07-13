import argparse
import base64
import dataclasses
import functools
import json
import tempfile
from configparser import RawConfigParser
from hashlib import md5
from os import environ
from pathlib import Path
from typing import Any, Callable

import dotenv
import finlab
import functions_framework
import keyring
from finlab.online.fugle_account import FugleAccount
from flask import Request
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from loguru import logger
from .create_f5project import create_f5project

__all__ = ["F5ProjectConfig", "F5Project", "create_f5project"]


class SimpleConfigParser(RawConfigParser):
    """A simple config parser

    It does not convert keys to lowercase and does not write empty lines.
    """

    def __init__(self):
        super().__init__()

    def optionxform(self, optionstr: str) -> str:
        return optionstr

    def from_dict(self, dictionary: dict) -> "SimpleConfigParser":
        for section, options in dictionary.items():
            self.add_section(section)
            self[section] = options

        return self

    def to_file(self, path: Path) -> None:
        with open(path, "w") as file:
            self.write(file)

        with open(path, "r") as file:
            lines = [line for line in file.readlines() if line.strip()]

        with open(path, "w") as file:
            file.writelines(lines)


@dataclasses.dataclass
class FugleCert:
    """Fugle certificate

    This makes it easier to manipulate a Fugle certificate and store it as a string,
    which is easier to store in environment variables.
    """

    string: str

    @classmethod
    def from_file(cls, path: Path) -> "FugleCert":
        bytes = path.read_bytes()
        bytes64 = base64.b64encode(bytes)
        string = bytes64.decode()
        return FugleCert(string)

    def to_file(self, path: Path) -> Path:
        bytes64 = self.string.encode()
        bytes = base64.b64decode(bytes64)
        path.write_bytes(bytes)
        return path

    @classmethod
    def from_string(cls, string: str) -> "FugleCert":
        return FugleCert(string)

    def to_string(self) -> str:
        return self.string


@dataclasses.dataclass
class FugleConfig:
    """Fugle configuration

    This makes it easier to dynamically generate a Fugle config file when you need it.
    """

    fugle_cert: str
    fugle_api_entry: str
    fugle_api_key: str
    fugle_api_secret: str
    fugle_account: str

    def to_file(self, data_dir: Path | None = None) -> Path:
        data_dir = data_dir or Path(tempfile.gettempdir())
        data_dir.mkdir(parents=True, exist_ok=True)

        cert_path = data_dir / "fugle-cert.p12"
        config_path = data_dir / "fugle-config.ini"

        logger.debug("Making Fugle certificate and config files")
        config_dict = {
            "Core": {"Entry": self.fugle_api_entry},
            "Cert": {"Path": str(FugleCert.from_string(self.fugle_cert).to_file(cert_path))},
            "Api": {"Key": self.fugle_api_key, "Secret": self.fugle_api_secret},
            "User": {"Account": self.fugle_account},
        }
        SimpleConfigParser().from_dict(config_dict).to_file(config_path)

        return config_path


@dataclasses.dataclass
class F5ProjectConfig:
    """F5Project configuration

    It contains the configuration required for F5Project.
    """

    BINARY_FILE_FIELDS = ("fugle_cert",)
    JSON_FIELDS = ("gcf_service_account", "repo_synced")

    finlab_api_token: str
    fugle_account: str
    fugle_password: str
    fugle_cert: str
    fugle_cert_password: str
    fugle_api_entry: str
    fugle_api_key: str
    fugle_api_secret: str
    fugle_market_api_key: str
    gcf_service_account: dict[str, str] | None = None
    repo_synced: dict[str, str] | None = None

    @classmethod
    @property
    def all_field_names(cls) -> tuple[str]:
        return tuple(f.name for f in dataclasses.fields(F5ProjectConfig))

    @classmethod
    def from_json_or_env(cls, json_path: Path) -> "F5ProjectConfig":
        if json_path.exists():
            return cls.from_json(json_path)
        else:
            return cls.from_env()

    @classmethod
    def from_json(cls, json_path: Path) -> "F5ProjectConfig":
        logger.debug(f"Getting `F5ProjectConfig` from `{json_path}`")
        all_values = json.loads(json_path.read_text())

        field_values = {}
        for f in F5ProjectConfig.all_field_names:
            v = all_values.get(f, None)
            if f in cls.BINARY_FILE_FIELDS:
                field_values[f] = FugleCert.from_file(json_path.parent / Path(v)).to_string()
            else:
                field_values[f] = v

        return F5ProjectConfig(**field_values)

    @classmethod
    def from_env(cls) -> "F5ProjectConfig":
        logger.debug("Get `F5ProjectConfig` from environment variables")
        all_values: Any = dict(environ)

        field_values = {}
        for f in F5ProjectConfig.all_field_names:
            v = all_values.get(f.upper(), None)
            if f in cls.JSON_FIELDS:
                field_values[f] = json.loads(v or "null")
            else:
                field_values[f] = v

        return F5ProjectConfig(**field_values)

    def to_fugle_config(self) -> FugleConfig:
        args = [
            self.fugle_cert,
            self.fugle_api_entry,
            self.fugle_api_key,
            self.fugle_api_secret,
            self.fugle_account,
        ]
        return FugleConfig(*args)


@dataclasses.dataclass
class F5Project:
    """F5 Project

    The main class for F5 Project. After initialization, call `setup` for configuring and logging in everything.
    After that, you can access `finlab.data` and call `fugle_account` to retrieve Fugle account instance as you need.

    The `call_gcf_endpoint` method calls the decorated function as a GCF endpoint locally.
    """

    config: F5ProjectConfig
    _gcf_endpoint: Callable | None = None
    _fugle_account: FugleAccount | None = None

    def __init__(self, config: F5ProjectConfig) -> None:
        self.config = config

    def setup(self, data_dir: Path | None = None) -> None:
        """A shortcut for `setup_finlab` and `setup_fugle`"""

        self.setup_finlab(data_dir)
        self.setup_fugle(data_dir)

    def setup_finlab(self, data_dir: Path | None = None) -> None:
        """Configuring and logging in Finlab"""

        logger.debug("Configuring and logging in Finlab")

        data_dir = data_dir if data_dir is not None else Path(tempfile.gettempdir())
        data_dir.mkdir(parents=True, exist_ok=True)

        storage_path = data_dir / "finlab_db"
        logger.debug(f"Using Finlab file storage at `{storage_path}`")
        storage = finlab.data.FileStorage(str(storage_path))
        finlab.data.set_storage(storage)

        logger.debug("Logging in Finlab with `finlab_api_token`")
        finlab.login(self.config.finlab_api_token)

    def setup_fugle(self, data_dir: Path | None = None) -> None:
        """Configuring and logging in Fugle"""

        logger.debug("Configuring and logging in Fugle")

        data_dir = data_dir if data_dir is not None else Path(tempfile.gettempdir())
        data_dir.mkdir(parents=True, exist_ok=True)

        logger.debug("Using `CryptFileKeyring` as keyring for Fugle login")
        file_keyring = CryptFileKeyring()
        raw_key = self.config.fugle_account
        hashed_key = md5(raw_key.encode("utf-8")).hexdigest()
        file_keyring.keyring_key = hashed_key
        keyring.set_keyring(file_keyring)
        keyring.set_password("fugle_trade_sdk:account", self.config.fugle_account, self.config.fugle_password)
        keyring.set_password("fugle_trade_sdk:cert", self.config.fugle_account, self.config.fugle_cert_password)

        config_path = self.config.to_fugle_config().to_file(data_dir)

        logger.debug(f"Logging in Fugle with config file `{config_path}` and `fugle_market_api_key`")
        fugle_account = FugleAccount(config_path, self.config.fugle_market_api_key)
        self._fugle_account = fugle_account

    def fugle_account(self) -> FugleAccount:
        """Get the Fugle account instance."""

        if self._fugle_account is None:
            raise ValueError("The project is not logged in yet. Please call `login` first.")

        return self._fugle_account

    def gcf_endpoint(self, func: Callable) -> Callable:
        """Decorator for registering a function as a GCF endpoint"""

        logger.debug(f"Registering `{func.__name__}` as GCF endpoint")

        if self._gcf_endpoint is not None:
            raise ValueError("Only one GCF endpoint is allowed")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from_request = len(args) == 1 and isinstance(args[0], Request)
            if from_request:
                request = args[0]
                payload = request.get_json(force=True)
                return func(**payload)

            return func(*args, **kwargs)

        self._gcf_endpoint = wrapper
        return wrapper

    def call_gcf_endpoint(self, directly: bool = False, params: dict = {}) -> Any:
        """Call the GCF endpoint

        If `directly = False`, simulate performing a request to the GCF endpoint.
        Otherwise, call the decorated function directly.

        If `params` is specified, pass it by request body or as `**params` according to `with_server`.

        They can also be specified by CLI arguments:
        - `--directly` or `-d` for `directly = True`
        - `--params '{"foo": "bar"}'` or `-p '{"foo": "bar"}'` for `params = {"foo": "bar"}`

        CLI arguments have higher priority than the arguments passed to this method.
        """

        if self._gcf_endpoint is None:
            raise ValueError("No GCF endpoint registered")

        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--directly", action="store_true", help="Call directly or not")
        parser.add_argument("-p", "--params", type=json.loads, help="Call with what params")
        args = parser.parse_args()

        directly = args.directly or directly
        params = args.params or params

        if directly:
            logger.info(f"Calling `{self._gcf_endpoint.__name__}` with `**params` where `params = {params}`")
            result = self._gcf_endpoint(**params)
        else:
            logger.info(f"Requesting `{self._gcf_endpoint.__name__}` with `json = {params}`")
            client = functions_framework.create_app(target=self._gcf_endpoint.__name__).test_client()
            response = client.post("/", json=params)
            result = response.get_json()

        logger.success(f"{result = }")
        return result

    def setup_github_secrets(self) -> None:
        """Set up GitHub secrets for the project

        To ensure the secrets are always up-to-date, you may want to call this method in your Git pre-push hook.
        """

        import github_secret_syncer

        config = self.config

        if config.repo_synced is None:
            raise ValueError("No `repo_synced` field in settings")

        if self._gcf_endpoint is None:
            raise ValueError("No GCF endpoint registered")

        dotenv_path = Path(tempfile.gettempdir()) / "temp.env"
        dotenv_path.write_text("")

        for f in config.all_field_names:
            if f in config.JSON_FIELDS:
                dotenv.set_key(dotenv_path, f.upper(), json.dumps(getattr(config, f)))
            else:
                dotenv.set_key(dotenv_path, f.upper(), getattr(config, f))

        dotenv.set_key(dotenv_path, "GCF_FUNCTION_TARGET", self._gcf_endpoint.__name__)

        logger.debug(f"Synchronizing secrets to {config.repo_synced['repo']} with dotenv file at {dotenv_path}")

        github_secret_syncer.sync_secrets(dotenv_path, **config.repo_synced, delete_missing=True)
