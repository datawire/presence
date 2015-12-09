# Copyright 2015 datawire. All rights reserved.
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
    -h --help           Show the help.
    --version           Show the version.
"""

import json
import netifaces
import os
import re
import yaml

from docopt import docopt
from presence import _metadata
from pykwalify.core import Core
from subprocess import Popen, check_output, STDOUT

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
            'sequence': [{
                'type': 'text',
                'unique': True,
            }]
        }
    }
}

def call_webservice(args):
    pass

def call_executable(command):
    out = check_output(command.split(), stderr=STDOUT, close_fds=True)
    return parse_response(str(out))

def parse_response(raw):
    return json.dumps(raw)

def update_watson_config(external_ip, paths, backup=True):
    from urlparse import urlsplit, urlunsplit

    for path in paths:
        doc = {}
        with open(path, 'r') as stream:
            doc = yaml.load(stream)

        parsed_url = urlsplit(doc['service']['url'])
        replaced_url = parsed_url._replace(netloc="{}:{}".format(external_ip, parsed_url.port))
        doc['service']['url'] = urlunsplit(replaced_url)

        with open(path, 'w+') as stream:
            yaml.dump(doc, stream)


def parse_lookup(text):

    """parses a lookup string such as net('eth0')

    :param text: the lookup string
    :return: a tuple pair of the parsed lookup_id and the provided args.
    """

    pattern = re.compile(r'^(echo|exec|inet|http)\((.*)\)$')
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

    if lookup_id == 'net':
        return netifaces.interfaces(args[0])[2][0]['addr']
    elif lookup_id == 'echo':
        return ','.join(args)
    elif lookup_id == 'exec':
        return 'NOT IMPLEMENTED'
    elif lookup_id == 'http':
        return 'NOT IMPLEMENTED'


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
