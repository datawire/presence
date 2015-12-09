# Copyright 2015 Datawire. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pytest
import responses

from presence import presence
from presence.presence import PresenceError

from pykwalify.errors import SchemaError
from mock import patch, MagicMock

test_data_path = os.path.join(os.path.dirname(__file__), 'data')

def fixture_path(name):

    """Gets the path to a test data fixture"""

    return os.path.join(test_data_path, name)

# ----------------------------------------------------------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------------------------------------------------------

def test_lookup_for_unknown():
    assert presence.lookup('NOT_A_REAL_LOOKUP_TYPE', []) == 'unknown'
    assert presence.lookup('NOT_A_REAL_LOOKUP_TYPE', ['foo', 'bar']) == 'unknown'

def test_lookup_for_echo():
    assert presence.lookup('echo', ['foo', 'bar', 'baz']) == 'foo,bar,baz'

@patch('presence.presence.call_http', MagicMock(return_value={'external_address': 'NOT_IMPORTANT'}))
def test_lookup_for_http():
    presence.lookup('http', ['GET', 'http://10.0.0.2/api/discover'])
    presence.call_http.assert_called_with(['GET', 'http://10.0.0.2/api/discover'])

@patch('presence.presence.call_executable', MagicMock(return_value={'external_address': 'NOT_IMPORTANT'}))
def test_lookup_for_exec():
    presence.lookup('exec', ['/opt/not/important/get_ip'])
    presence.call_executable.assert_called_with(['/opt/not/important/get_ip'])

def test_validate_result_fails_with_invalid_date():
    with pytest.raises(PresenceError) as se:
        presence.validate_result({'not_the_correct_key': 'foobar'})

def test_validate_result_succeeds():
    assert presence.validate_result({'external_address': '10.0.0.2'}) == {'external_address': '10.0.0.2'}

@responses.activate
def test_raise_error_if_call_http_result_is_invalid_structure():
    responses.add(responses.GET, 'http://10.0.0.1/api/foo/bar', status=200, body='{}')
    with pytest.raises(PresenceError) as pe:
        presence.call_http('GET', 'http://10.0.0.1/api/foo/bar')

@responses.activate
def test_raise_error_if_call_http_result_is_invalid_structure():
    responses.add(responses.GET, 'http://10.0.0.1/api/foo/bar', status=200, body='{"external_address": "10.0.0.2"}')
    data = presence.call_http('GET', 'http://10.0.0.1/api/foo/bar')
    assert data == {'external_address': '10.0.0.2'}

def test_raise_error_if_call_http_fails():
    pass

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
