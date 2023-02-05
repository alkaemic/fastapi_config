import json
import os
from dotenv import load_dotenv
from typing import Optional

__all__ = ["Config", "ConfigMeta", "Field"]

__version__ = "1.0.0"

#: A string value indicating that the type of the field is "JSON",
JSON = "JSON"


class Field:
    """Class for definining a field on a Config class

    Args:
        default: the default value for this field
        type: the type of this field; can be a python type (e.g. int, bool) or
            Config.JSON for JSON data
        env_var (str): name of the environment variable to populate this field
    """

    def __init__(self, default, field_type=str, env_var=None):
        self.default = default
        self.type = field_type
        self._env_var = env_var

    @property
    def value(self):
        """Get the current value of this field

        Checks the related environment variable; otherwise returns the default
        value
        """
        raw_val = os.environ.get(self._env_var)
        if raw_val is None:
            return self.default

        if self.type == bool:
            if raw_val.lower() == "true":
                return True
            if raw_val.lower() == "false":
                return False
            raise ValueError("Bool type must be TRUE or FALSE")

        if self.type == JSON:
            return json.loads(raw_val)

        return self.type(raw_val)

    @property
    def env_var(self):
        return self._env_var

    @env_var.setter
    def env_var(self, value):
        if not self._env_var:
            self._env_var = value.upper()

    def __repr__(self):
        return f"Field({self.default}, field_type={self.type}, env_var={self._env_var})"


class ConfigMeta(type):
    """Config Metaclass

    Binds `Field` fields to the `_vars` attribute, which is a dictionary mapping
    field names to the associated `Field` object
    """

    def __new__(mcs, name, bases, attrs):
        cls = super(ConfigMeta, mcs).__new__(mcs, name, bases, attrs)
        cls._vars = {}

        #: Get all of the classes in the class hierarchy in the reverse
        #: method-resolution order, i.e. starting with ``object```, work up the
        #: class hierarchy. [SWQ]
        reversed_mro = list(cls.__mro__)
        reversed_mro.reverse()

        #: Preserve any fields that have been extracted out from earlier config
        #: instantiations that are ancestors of the current one. [SWQ]
        for mro_class in reversed_mro:
            try:
                cls._vars.update(mro_class._vars)
            except Exception:
                pass

        for name, attr in list(attrs.items()):
            if isinstance(attr, Field):
                cls._vars[name] = attr
                cls._vars[name].env_var = name
                delattr(cls, name)
        return cls


class Config(metaclass=ConfigMeta):
    """Base Config class for defining configuration objects

    Example:
        ```
        from lib.config import Config, Field

        class ExampleConfig(Config):
            some_value = Field(default="value")
            some_other_value = Field(default=20, field_type=int)
            third_value = Field(default="3rd value", env_var="THIRD")

        config = ExampleConfig(env_path="./.env")
        ```

        You can access the defined fields on the object:

        ```
        >>> config.some_value
        "value"
        >>> config.some_other_value
        20
        ```

        You can override default values by setting an associated environment
        variable. By default the environment variable is the same name as the
        field in all uppercase. This can be overridden with the `env_var` parameter
        to the `Field` field:

        ```
        # SOME_VALUE=a different value
        >>> config.some_value
        "a different value"
        # THIRD=third
        >>> config.third_value
        "third"
        ```
    """

    def __init__(self, config: Optional[dict] = None, env_path=None):
        """Initialize Config object

        Args:
            env_path (str): path to .env file to load
        """
        if config:
            for key, value in config.items():
                self.__dict__[key] = Field(value)
                print(self.__dict__)

        #: TODO: This will only read the .env file when this class is first
        #:       instantiated. This could pose a problem for "hot reloading"
        #:       without a full deploy start/stop. [SWQ]
        load_dotenv(dotenv_path=env_path, verbose=True)

    def __getattr__(self, name):
        if name in self._vars:
            return self._vars[name].value
        raise AttributeError("No config variable named {}".format(name))

    def as_dict(self) -> dict:
        """Create a dictionary from this object"""
        return {k: var.value for k, var in self._vars.items()}

    def get(self, name, default=None):
        _d = self.as_dict()
        return _d.get(name, None)

    def has_key(self, name: str) -> bool:
        _d = self.as_dict()
        return name in _d

    def dump(self):
        print("")
        print("================ CONFIGURATION ================")
        print("")
        config_items = self.as_dict()
        for config_name, value in config_items.items():
            print(f"  {config_name} : {value}")
        print("")
