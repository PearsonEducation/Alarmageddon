import pytest
from alarmageddon.config import Config


@pytest.fixture
def conf():
    return ({"environment": {
            "prod": {
                "hosts": {
                    "service": {
                        "url": "http://www.prod.com"
                    }
                }
            },
            "stable": {
                "hosts": {
                    "service": {
                        "url": "http://www.stable.com"
                    }
                }
            }
        },
        "foo": "bar",
        "name": "fozzie",
        "age": 52,
        "sub": {
            "value": 42
        }
    })


def test_config_gets_simple_value(conf):
    c = Config(conf, "prod")
    assert c["foo"] == 'bar'


def test_config_gets_missing_value(conf):
    c = Config(conf, "prod")
    with pytest.raises(KeyError):
        c["missing"]


def test_config_gets_missing_value_as_none(conf):
    c = Config(conf, "prod")
    assert c.get("missing") is None


def test_config_gets_nested_value(conf):
    c = Config(conf, "prod")
    assert c["sub"]["value"] == 42


def test_config_returns_keys(conf):
    c = Config(conf, "prod")
    assert c.keys() == conf.keys()


def test_config_returns_values(conf):
    c = Config(conf, "prod")
    assert c.values() == conf.values()


def test_config_correct_environment(conf):
    c = Config(conf, "prod")
    assert c.environment_name() == "prod"


def test_config_incorrect_environment(conf):
    c = Config(conf, "prod")
    with pytest.raises(ValueError):
        c = Config(conf, "foo")


def test_config_gets_correct_host_prod(conf):
    c = Config(conf, "prod")
    assert c.hostname("service") == "http://www.prod.com"


def test_config_gets_correct_host_stable(conf):
    c = Config(conf, "stable")
    assert c.hostname("service") == "http://www.stable.com"


def test_config_gets_correct_host_bad_service(conf):
    c = Config(conf, "stable")
    with pytest.raises(KeyError):
        c.hostname("wrong")
