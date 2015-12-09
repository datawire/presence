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

"""presence

Presence is a runtime environment discovery program.

Usage:
    presence [options]
    presence (-h | --help)
    presence --version

Options:
    -c --config=<file>  Set the configuration file [default: /etc/datawire/presence.yml]
    --lookup=<lookup>   Add hoc support for performing a lookup
    -h --help           Show the help.
    --version           Show the version.
"""

import json
import netifaces
import os
import re
import requests
import yaml
import _metadata

from docopt import docopt
from pykwalify.core import Core
from pykwalify.errors import SchemaError
from subprocess import Popen, check_output, STDOUT

# schema for the configuration format used by the program.
config_schema = {
    'type': 'map',
    'mapping': {
        'lookup': {
            'type': 'text',
            'required': True
        },
        'watson_configs': {
            'type': 'seq',
            'required': True,
            'range': {'min': 1, 'max': 1000},
            'sequence': [
                {'type': 'text', 'unique': True}
            ]
        },
        'backup_watson_configs': {
            'type': 'bool'
        }
    }
}

# schema for data sent into the program from an external source such as URL, program plugin, or standard input.
result_schema = {
    'type': 'map',
    'mapping': {
        'external_address': {'type': 'text', 'required': True}
    }
}

class PresenceError(Exception):
    pass

def validate_result(data):
    try:
        validator = Core(source_data=data, schema_data=result_schema)
        validator.validate(raise_exception=True)
    except SchemaError as se:
        raise PresenceError(se)

    return data

def get_network_interface_address(name):

    """Queries a local network interface for its IP address.

    Args:
        name: The name of the network address (e.g. 'eth0')

    Raises:
        PresenceError: If the returned data is invalid.
    """

    external_address = netifaces.interfaces(name)[2][0]['addr']
    return {'external_address': external_address}

def call_http(method, url):

    """Invokes a HTTP(S) URL to retrieve the network address.

    Args:
        method: The HTTP method to use.
        url: The URL to query.

    Returns:
        A dictionary containing a single-key "external_address" that indicates the host machines IP.

    Raises:
        PresenceError: Raised if the returned data is invalid or the call fails for some reason.
    """

    resp = requests.request(method, url)
    data = resp.json()
    return validate_result(data)


def call_executable(command):

    """Invokes an external program to retrieve the network address.

    Args:
        command: The full command to run.

    Returns:
        A dictionary containing a single-key "external_address" that indicates the host machines IP.

    Raises:
        PresenceError: Raised if the returned data is invalid or the call fails for some reason.
    """

    out = check_output(command, stderr=STDOUT, close_fds=True)
    return validate_result(json.dumps(out if not None else '{}'))


def update_watson_config(external_address, paths, backup=False):

    """Updates a Watson configuration file.

    Replaces the host information in the Watson service URL with a network address that is known to be public.

    Args:
        external_address: The address that is reachable.
        paths: A list of one or more Datawire Watson configuration files.
        backup: Whether the file being modified should be backed up before modification

    Returns:
        A dictionary containing a single-key "external_address" that indicates the host machines IP.

    Raises:
        PresenceError: Raised if a configuration file cannot be updated for some reason.
    """

    from urlparse import urlsplit, urlunsplit
    from shutil import copyfile

    for path in paths:
        if backup:
            copyfile(path, path + '.bak')

        doc = {}
        with open(path, 'r') as stream:
            doc = yaml.load(stream)

        parsed_url = urlsplit(doc['service']['url'])
        replaced_url = parsed_url._replace(netloc="{}:{}".format(external_address, parsed_url.port))
        doc['service']['url'] = urlunsplit(replaced_url)

        with open(path, 'w+') as stream:
            yaml.dump(doc, stream)


def parse_lookup(text):

    """Parse a lookup function into its name and argument list.

    Args:
        text: The raw text

    Returns:
        A tuple in the format (lookup_name, lookup_args). The lookup arguments can be an empty list if there were none
        provided

    Raises:
        ValueError: If the lookup function cannot be parsed.
    """

    pattern = re.compile(r'^(echo|exec|net|url)\((.*)\)$')
    match = pattern.match(text)
    if match:
        lookup_id, raw_args = pattern.match(text).groups()
        if raw_args is None:
            raw_args = []
        else:
            raw_args = raw_args.split(',')

        return lookup_id, [x.strip() for x in raw_args]
    else:
        raise ValueError('unable to parse lookup (lookup: {})'.format(text))


def lookup(lookup_id, *args):

    """executes the specified lookup by ID with the provided arguments

    :param lookup_id:
    :param args:
    :return:
    """

    switch = {
        'net': get_network_interface_address,
        'echo': lambda: ','.join(args),
        'exec': call_executable,
        'url': call_http
    }

    func = switch.get(lookup_id, lambda: 'unknown')
    return func(*args)


def load_config(path):

    """validates, loads and configures the yaml document at the specified path

    :param path: the path to the file
    :return: the parsed yaml document
    :raises SchemaError: if the yaml document does not validate
    """

    validator = Core(source_file=path, schema_data=config_schema)
    validator.validate(raise_exception=True)

    pattern = re.compile(r'^(.*)<%= ENV\[\'(.*)\'\] %>(.*)$')
    yaml.add_implicit_resolver('!env_regex', pattern)

    def env_regex(loader, node):
        value = loader.construct_scalar(node)
        front, variable_name, back = pattern.match(value).groups()
        return str(front) + os.environ[variable_name] + str(back)

    yaml.add_constructor('!env_regex', env_regex)

    with open(path, 'r') as stream:
        doc = yaml.load(stream)
        return doc


def run_presence(args):
    config = load_config(args['--config'])

    lookup_id, lookup_args = parse_lookup(config['lookup'])
    address = lookup(lookup_id, str(lookup_args).split(','))
    update_watson_config(address, list(config['watson_configs']))

def main(argv):
    exit(run_presence(docopt(__doc__, argv=argv, version="presence {0}".format(_metadata.__version__))))

if __name__ == "__main__":
    import sys
    main(sys.argv)
