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

__all__ = ["F5ProjectConfig", "F5Project"]


# Private
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

    @classmethod
    def from_f5project_config(cls, config: "F5ProjectConfig") -> "FugleConfig":
        fugle_cert = config.fugle_cert
        fugle_api_entry = config.fugle_api_entry
        fugle_api_key = config.fugle_api_key
        fugle_api_secret = config.fugle_api_secret
        fugle_account = config.fugle_account
        return FugleConfig(fugle_cert, fugle_api_entry, fugle_api_key, fugle_api_secret, fugle_account)

    def to_file(self, data_dir: Path | None = None) -> Path:
        data_dir = data_dir or Path(tempfile.gettempdir())
        data_dir.mkdir(parents=True, exist_ok=True)

        cert_path = data_dir / "fugle-cert.p12"
        config_path = data_dir / "fugle-config.ini"

        logger.info("Making Fugle certificate and config files")
        config_dict = {
            "Core": {"Entry": self.fugle_api_entry},
            "Cert": {"Path": str(FugleCert.from_string(self.fugle_cert).to_file(cert_path))},
            "Api": {"Key": self.fugle_api_key, "Secret": self.fugle_api_secret},
            "User": {"Account": self.fugle_account},
        }
        SimpleConfigParser().from_dict(config_dict).to_file(config_path)
        return config_path


# Public
@dataclasses.dataclass
class F5ProjectConfig:
    """F5Project configuration

    It contains all the configuration items required for F5Project.

    The `sync_github_secrets` method is convenient for syncing the configuration to GitHub secrets.
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
        logger.info(f"Get `F5ProjectConfig` from `{json_path}`")
        all_values = json.loads(json_path.read_text())

        field_values = {}
        for f in F5ProjectConfig.all_field_names():
            v = all_values.get(f, None)
            if f in cls.BINARY_FILE_FIELDS:
                field_values[f] = FugleCert.from_file(json_path.parent / Path(v)).to_string()
            else:
                field_values[f] = v

        return F5ProjectConfig(**field_values)

    @classmethod
    def from_env(cls) -> "F5ProjectConfig":
        logger.info("Get `F5ProjectConfig` from environment variables")
        all_values: Any = dict(environ)

        field_values = {}
        for f in F5ProjectConfig.all_field_names():
            v = all_values.get(f.upper(), None)
            if f in cls.JSON_FIELDS:
                field_values[f] = json.loads(v or "null")
            else:
                field_values[f] = v

        return F5ProjectConfig(**field_values)

    def sync_github_secrets(self, gcf_function_target: str) -> None:
        import github_secret_syncer

        dotenv_path = Path(tempfile.gettempdir()) / "temp.env"
        dotenv_path.write_text("")
        for f in F5ProjectConfig.all_field_names():
            if f in self.JSON_FIELDS:
                dotenv.set_key(dotenv_path, f.upper(), json.dumps(getattr(self, f)))
            else:
                dotenv.set_key(dotenv_path, f.upper(), getattr(self, f))

        dotenv.set_key(dotenv_path, "GCF_FUNCTION_TARGET", gcf_function_target)

        if self.repo_synced is None:
            raise ValueError("No `repo_synced` field in settings")

        logger.info(f"Syncing secrets to {self.repo_synced['repo']} with dotenv file at {dotenv_path}")
        github_secret_syncer.sync_secrets(dotenv_path, **self.repo_synced, delete_missing=True)


@dataclasses.dataclass
class F5Project:
    """F5 Project

    The main class for F5 Project. After initialization, call `login` to log in Finlab and Fugle.

    The `login` method will also do some pre-processing, including:
    - Setting up Finlab file storage
    - Setting up Fugle certificate and config files

    After logging in, you can access `finlab.data` and call `get_fugle_account` to trade with Fugle APIs.

    The `run` method will request/call the `@gcf_function` decorated function locally.
    """

    config: F5ProjectConfig
    _gcf_endpoint: Callable | None = None
    _fugle_account: FugleAccount | None = None

    def __init__(self, config: F5ProjectConfig) -> None:
        self.config = config

    def login(self, data_dir: Path | None = None) -> None:
        # Pre-process
        data_dir = data_dir or Path(tempfile.gettempdir())
        data_dir.mkdir(parents=True, exist_ok=True)

        # Configure Finlab
        finlab_storage_path = data_dir / "finlab_db"
        logger.info(f"Configuring Finlab, setting up file storage at `{finlab_storage_path}`")
        storage = finlab.data.FileStorage(str(finlab_storage_path))
        finlab.data.set_storage(storage)

        # Log in Finlab
        logger.info("Logging in Finlab with `self.config.finlab_api_token`")
        finlab.login(self.config.finlab_api_token)

        # Configure Fugle
        logger.info("Configuring Fugle")

        # Set keyring
        file_keyring = CryptFileKeyring()
        raw_key = self.config.fugle_account
        hashed_key = md5(raw_key.encode("utf-8")).hexdigest()
        file_keyring.keyring_key = hashed_key
        keyring.set_keyring(file_keyring)
        keyring.set_password("fugle_trade_sdk:account", self.config.fugle_account, self.config.fugle_password)
        keyring.set_password("fugle_trade_sdk:cert", self.config.fugle_account, self.config.fugle_cert_password)

        # Make Fugle certificate and config files
        config_path = FugleConfig.from_f5project_config(self.config).to_file(data_dir)

        # Log in Fugle
        logger.info(f"Logging in Fugle with `{config_path}` and `self.config.fugle_market_api_key`")
        fugle_account = FugleAccount(config_path, self.config.fugle_market_api_key)
        self._fugle_account = fugle_account

    def get_fugle_account(self) -> FugleAccount:
        if self._fugle_account is None:
            raise ValueError("The project is not logged in yet. Please call `login` first.")

        return self._fugle_account

    def sync_github_secrets(self) -> None:
        if self._gcf_endpoint is None:
            raise ValueError("No GCF endpoint registered")

        self.config.sync_github_secrets(gcf_function_target=self._gcf_endpoint.__name__)

    def gcf_endpoint(self, func):
        logger.info(f"Registering `{func.__name__}` as GCF endpoint")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from_request = len(args) > 0 and isinstance(args[0], Request)
            if from_request:
                request = args[0]
                payload = request.get_json(force=True)
                return func(**payload)
            else:
                return func(*args, **kwargs)

        if self._gcf_endpoint is None:
            self._gcf_endpoint = wrapper
        else:
            raise ValueError("Only one GCF endpoint is allowed")
        return wrapper

    def run_locally(self, with_server: bool | None = None, params: dict | None = None) -> Any:
        """Request/call the GCF function locally

        When `with_server` is `True`, it will simulate performing a request to the GCF endpoint.
        Otherwise, it will call the GCF function directly.

        When `params` is specified, it will be passed to the GCF function as JSON.

        CLI args `--with-server` (`-w`) and `--params` (`-p`) will be used,
        if the arguments are not specified explicitly.
        """
        if self._gcf_endpoint is None:
            raise ValueError("No GCF endpoint registered")

        # Get args from CLI
        parser = argparse.ArgumentParser()
        parser.add_argument("-w", "--with-server", action="store_true", help="Run with server or not")
        parser.add_argument("-p", "--params", type=json.loads, default={}, help="Run with these JSON params")
        args = parser.parse_args()

        # If not specified, use args
        with_server = with_server if with_server is not None else args.with_server
        params = params if params is not None else args.params
        logger.debug(f"`{with_server = }`, `{params = }`")

        if with_server:
            # Request GCF endpoint
            logger.debug(f"Requesting `{self._gcf_endpoint.__name__}` with `json = {params}`")
            client = functions_framework.create_app(target=self._gcf_endpoint.__name__).test_client()
            response = client.post("/", json=params)
            result = response.get_json()
        else:
            # Call decorated function directly
            logger.debug(f"Calling `{self._gcf_endpoint.__name__}` with `{params}` as kwargs")
            result = self._gcf_endpoint(**params)

        logger.success(f"{result = }")
        return result
