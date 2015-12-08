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

import abc
import os
import re
import yaml

from docopt import docopt
from pykwalify.core import Core

config_schema = {
    'type': 'map',
    'mapping': {
        'type': {'type': 'text', 'required': True},
        'custom': {'type': 'text'}
    }
}

class PresenceInfo(object):
    pass

class Discoverer(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def discover(self):
        return

class PresenceConfig(yaml.YAMLObject):

    yaml_tag = u'!PresenceConfig'

    def __init__(self, env_type, env_plugin=None):
        self.env_type = env_type
        self.env_plugin = env_plugin



class Presence(object):

    def __init__(self, discoverer):
        self.discoverer = discoverer

    def discover(self):
        return self.discoverer.discover()

    def save(self):
        pass

def load_config(path):
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

def main(argv):
    exit(run_presence(docopt(__doc__, argv=argv, version="presence {0}".format('dev'))))

if __name__ == "__main__":
    pass
