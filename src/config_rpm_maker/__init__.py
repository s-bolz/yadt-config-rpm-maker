#   yadt-config-rpm-maker
#   Copyright (C) 2011-2013 Immobilien Scout GmbH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""yadt-config-rpm-maker

Usage:
  config-rpm-maker <repository> <revision> [--debug]
  config-rpm-maker -h | --help
  config-rpm-maker --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --debug       Force DEBUG log level.
"""
import sys
import traceback

from docopt import docopt
from logging import DEBUG, Formatter, StreamHandler, getLogger

print "import config"
from config_rpm_maker import config
print "import config - ok"

print "import ConfigRpmMaker"
from config_rpm_maker.configRpmMaker import ConfigRpmMaker
print "import ConfigRpmMaker - ok"

print "Import BaseConfigRpmMakerException"
from config_rpm_maker.exceptions import BaseConfigRpmMakerException
print "Import BaseConfigRpmMakerException - ok"

print "Import SvnService"
from config_rpm_maker.svn import SvnService
print "Import SvnService - ok"

ARGUMENT_REVISION = '<revision>'
ARGUMENT_REPOSITORY = '<repository>'

OPTION_DEBUG = '--debug'

LOGGING_FORMAT = "[%(levelname)5s] %(message)s"
ROOT_LOGGER_NAME = "config_rpm_maker"


def create_root_logger(log_level=config.DEFAULT_LOG_LEVEL):
    """ Returnes a root_logger which logs to the console using the given log_level. """
    formatter = Formatter(LOGGING_FORMAT)

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger = getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    return root_logger


def main():
    arguments = docopt(__doc__, version='yadt-config-rpm-maker 2.0')
    try:
        config.load_configuration_file()

        if arguments[OPTION_DEBUG]:
            LOGGER = create_root_logger(DEBUG)
        else:
            log_level = config.get_log_level()
            LOGGER = create_root_logger(log_level)

    except config.ConfigException as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    LOGGER.debug('Arguments are: %s', str(arguments))
    LOGGER.debug('Loaded configuration file "%s": %s', config.configuration_file_path, str(config.configuration))

    revision = arguments[ARGUMENT_REVISION]
    if not revision.isdigit():
        LOGGER.error('Given revision "%s" is not a integer.', revision)
        sys.exit(1)

    repository = arguments[ARGUMENT_REPOSITORY]

    try:
        # first use case is post-commit hook. repo dir can be used as file:/// SVN URL
        svn_service = SvnService(base_url='file://{0}'.format(repository),
                                 path_to_config=config.get('svn_path_to_config'))
        ConfigRpmMaker(revision=revision, svn_service=svn_service).build()

    except BaseConfigRpmMakerException as e:
        for line in str(e).split("\n"):
            LOGGER.error(line)
        sys.exit(1)

    except Exception:
        traceback.print_exc(5)
        sys.exit(2)
