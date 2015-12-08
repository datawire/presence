import os
import pytest

from presence import presence
from pykwalify.errors import SchemaError

test_data_path = os.path.join(os.path.dirname(__file__), 'data')

def fixture_path(name):
    return os.path.join(test_data_path, name)

def test_validates_and_load_valid_config_ok():
    data = presence.load_config(fixture_path('config_valid.yml'))
    assert data == {'type': 'ec2'}

def test_validates_and_load_valid_config_custom_ok():
    data = presence.load_config(fixture_path('config_valid_with_custom.yml'))
    assert data == {'type': 'custom', 'custom': 'file:///the/path/is/absolutely/irrelevant'}

def test_fail_to_load_invalid_scheme():
    with pytest.raises(SchemaError) as e:
        presence.load_config(fixture_path('config_invalid.yml'))

def test_config_parses_in_environment_variable():
    os.environ['presence_test_environment_id'] = 'foo'
    data = presence.load_config(fixture_path('config_valid_with_env_var.yml'))
    assert data == {'type': 'quux_foobar'}
