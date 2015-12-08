import os
import pytest

from presence import presence
from pykwalify.errors import SchemaError

test_data_path = os.path.join(os.path.dirname(__file__), 'data')

def fixture_path(name):
    return os.path.join(test_data_path, name)

def test_parse_lookup():
    for actual, expected in {
        "echo(bar)": {'lookup_name': 'echo', 'lookup_args': ['bar']},
        "echo(bar, baz)": {'lookup_name': 'echo', 'lookup_args': ['bar', 'baz']},
        "echo(bar, baz, boz)": {
            'lookup_name': 'echo',
            'lookup_args': ['bar', 'baz', 'boz']}
    }.iteritems():
        out_name, out_args = presence.parse_lookup(actual)
        assert out_name == expected['lookup_name']
        assert out_args == expected['lookup_args']

def test_fail_parse_lookup_invalid_lookup_name():
    with pytest.raises(ValueError) as e:
        name, args = presence.parse_lookup('foo(bar)')


def test_validates_and_load_valid_config_ok():
    data = presence.load_config(fixture_path('config_valid.yml'))
    assert data == {
        'lookup': "net('eth0')",
        'watson_configs': [
            '/etc/datawire/watson-foo.yml',
            '/etc/datawire/watson-bar.yml'
        ]}

def test_fail_because_watson_configs_are_not_unique():
    with pytest.raises(SchemaError) as e:
        presence.load_config(fixture_path('config_invalid_duplicate_watson_configs.yml'))

def test_fail_to_load_config_missing_watson_config_paths():
    with pytest.raises(SchemaError) as e:
        presence.load_config(fixture_path('config_invalid_missing_watson_configs.yml'))

def test_fail_to_load_invalid_scheme():
    with pytest.raises(SchemaError) as e:
        presence.load_config(fixture_path('config_invalid.yml'))


def test_config_parses_in_environment_variable():
    os.environ['DW_PRESENCE_LOOKUP'] = "net('eth0')"
    data = presence.load_config(fixture_path('config_valid_with_env_var.yml'))
    assert data == {
        'lookup': "net('eth0')",
        'watson_configs': [
            '/etc/datawire/watson-foo.yml',
            '/etc/datawire/watson-bar.yml'
        ]}
