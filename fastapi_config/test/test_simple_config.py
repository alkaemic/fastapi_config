import pytest
from .. import Config, Field, JSON


class SampleConfig(Config):
    foo = Field(default=True, field_type=bool)
    bar = Field(default="bar")
    baz = Field(default=25, field_type=int, env_var="QUUX")
    some_obj = Field(
        default={
            "some_int": 5,
            "some_str": "str",
            "some_bool": True,
            "some_list": [1, 2, 3],
        },
        field_type=JSON,
    )


@pytest.fixture
def config():
    return SampleConfig()


def test_config_default_values(config):
    assert config.foo is True
    assert config.bar == "bar"
    assert config.baz == 25
    assert config.some_obj == {
        "some_int": 5,
        "some_str": "str",
        "some_bool": True,
        "some_list": [1, 2, 3],
    }


def test_default_environment_variables(config, monkeypatch):
    monkeypatch.setenv("FOO", "False")
    monkeypatch.setenv("BAR", "something else")
    monkeypatch.setenv("QUUX", "10")

    assert config.foo is False
    assert config.bar == "something else"
    assert config.baz == 10


def test_json_environment_variables(config, monkeypatch):
    monkeypatch.setenv(
        "SOME_OBJ",
        """{
            "some_int": 22,
            "some_str": "another_string",
            "some_bool": false,
            "some_list": ["foo", "bar", "baz"]
        }""",
    )
    expected = {
        "some_int": 22,
        "some_str": "another_string",
        "some_bool": False,
        "some_list": ["foo", "bar", "baz"],
    }

    assert config.some_obj == expected


def test_manual_environment_variables(config, monkeypatch):
    monkeypatch.setenv("QUUX", "30")
    assert config.baz == 30


def test_get_dict(config):
    expected = {
        "foo": True,
        "bar": "bar",
        "baz": 25,
        "some_obj": {
            "some_int": 5,
            "some_str": "str",
            "some_bool": True,
            "some_list": [1, 2, 3],
        },
    }
    config_dict = config.as_dict()
    assert config_dict == expected
