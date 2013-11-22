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


import traceback

from logging import DEBUG, getLogger
from math import ceil
from optparse import OptionParser
from sys import argv, exit, stderr, stdout
from time import time, strftime
from urlparse import urlparse

from config_rpm_maker import config
from config_rpm_maker.config import (DEFAULT_DATE_FORMAT,
                                     DEFAULT_CONFIG_VIEWER_ONLY,
                                     DEFAULT_RPM_UPLOAD_CMD,
                                     KEY_SVN_PATH_TO_CONFIG,
                                     KEY_RPM_UPLOAD_CMD,
                                     KEY_CONFIG_VIEWER_ONLY)
from config_rpm_maker.configRpmMaker import ConfigRpmMaker
from config_rpm_maker.exceptions import BaseConfigRpmMakerException
from config_rpm_maker.logutils import (create_console_handler,
                                       create_sys_log_handler,
                                       log_configuration,
                                       log_process_id)
from config_rpm_maker.svnservice import SvnService


ARGUMENT_REPOSITORY = '<repository-url>'
ARGUMENT_REVISION = '<revision>'

USAGE_INFORMATION = """Usage: %prog repo-url revision [options]

Arguments:
  repo-url    URL to subversion repository or absolute path on localhost
  revision    subversion revision for which the configuration rpms are going to be built"""

OPTION_DEBUG = '--debug'
OPTION_DEBUG_HELP = "force DEBUG log level on console"

OPTION_NO_SYSLOG = '--no-syslog'
OPTION_NO_SYSLOG_HELP = "switch logging of debug information to syslog off"

OPTION_VERSION = '--version'
OPTION_VERSION_HELP = "show version"

OPTION_RPM_UPLOAD_CMD = '--rpm-upload-cmd'
OPTION_RPM_UPLOAD_CMD_HELP = 'Overwrite rpm_upload_config in config file'

OPTION_CONFIG_VIEWER_ONLY = '--config-viewer-only'
OPTION_CONFIG_VIEWER_ONLY_HELP = 'Only generated files for config viewer. Skip RPM build and upload.'

MESSAGE_SUCCESS = "Success."

RETURN_CODE_SUCCESS = 0
RETURN_CODE_VERSION = RETURN_CODE_SUCCESS
RETURN_CODE_NOT_ENOUGH_ARGUMENTS = 1
RETURN_CODE_REVISION_IS_NOT_AN_INTEGER = 2
RETURN_CODE_CONFIGURATION_ERROR = 3
RETURN_CODE_EXCEPTION_OCCURRED = 4
RETURN_CODE_UNKOWN_EXCEPTION_OCCURRED = 5
RETURN_CODE_REPOSITORY_URL_INVALID = 6

VALID_REPOSITORY_URL_SCHEMES = ['http', 'https', 'file', 'ssh', 'svn']

LOGGER = getLogger(__name__)


timestamp_at_start = 0


def start_measuring_time():
    """ Start measuring the time. This is required to calculate the elapsed time. """
    LOGGER.info("Starting to measure time at %s", strftime(DEFAULT_DATE_FORMAT))

    global timestamp_at_start
    timestamp_at_start = time()


def exit_program(message, return_code):
    """ Logs the given message and exits with given return code. """

    elapsed_time_in_seconds = time() - timestamp_at_start
    elapsed_time_in_seconds = ceil(elapsed_time_in_seconds * 100) / 100
    LOGGER.info('Elapsed time: {0}s'.format(elapsed_time_in_seconds))

    if return_code == RETURN_CODE_SUCCESS:
        LOGGER.info(message)
    else:
        LOGGER.error(message)

    exit(return_code)


def parse_arguments(argv, version):
    """
        Parses the given command line arguments.

        if -h or --help is given it will display the print the help screen and exit
        if OPTION_VERSION is given it will display the version information and exit

        Otherwise it will return a dictionary containing the keys and values for
            OPTION_DEBUG: boolean, True if option --debug is given
            OPTION_NO_SYSLOG: boolean, True if option --no-syslog is given
            KEY_RPM_UPLOAD_CMD: string, command executed for rpm uploads
            KEY_CONFIG_VIEWER_ONLY, boolean, True to indicate rpm building and uploads are skipped
            ARGUMENT_REPOSITORY: string, the first argument
            ARGUMENT_REVISION: string, the second argument
    """

    usage = USAGE_INFORMATION
    parser = OptionParser(usage=usage)
    parser.add_option("", OPTION_DEBUG,
                      action="store_true", dest="debug", default=False,
                      help=OPTION_DEBUG_HELP)
    parser.add_option("", OPTION_NO_SYSLOG,
                      action="store_true", dest="no_syslog", default=False,
                      help=OPTION_NO_SYSLOG_HELP)
    parser.add_option("", OPTION_VERSION,
                      action="store_true", dest="version", default=False,
                      help=OPTION_VERSION_HELP)
    parser.add_option("", OPTION_RPM_UPLOAD_CMD,
                      dest=KEY_RPM_UPLOAD_CMD, default=config.get(KEY_RPM_UPLOAD_CMD, DEFAULT_RPM_UPLOAD_CMD),
                      help=OPTION_RPM_UPLOAD_CMD_HELP)
    parser.add_option("", OPTION_CONFIG_VIEWER_ONLY,
                      action="store_true", dest=KEY_CONFIG_VIEWER_ONLY, default=config.get(KEY_CONFIG_VIEWER_ONLY, DEFAULT_CONFIG_VIEWER_ONLY),
                      help=OPTION_CONFIG_VIEWER_ONLY_HELP)
    values, args = parser.parse_args(argv)

    if values.version:
        stdout.write(version + '\n')
        return exit(RETURN_CODE_VERSION)

    if len(args) < 2:
        parser.print_help()
        return exit(RETURN_CODE_NOT_ENOUGH_ARGUMENTS)

    arguments = {OPTION_DEBUG: values.debug or False,
                 OPTION_NO_SYSLOG: values.no_syslog or False,
                 KEY_RPM_UPLOAD_CMD: values[KEY_RPM_UPLOAD_CMD],
                 KEY_CONFIG_VIEWER_ONLY: values[KEY_CONFIG_VIEWER_ONLY],
                 ARGUMENT_REPOSITORY: args[0],
                 ARGUMENT_REVISION: args[1]}

    return arguments


def determine_console_log_level(arguments):
    """ Determines the log level based on arguments and configuration """
    try:
        if arguments[OPTION_DEBUG]:
            log_level = DEBUG
        else:
            log_level = config.get_log_level()

    except config.ConfigException as e:
        stderr.write(str(e) + "\n")
        exit(RETURN_CODE_CONFIGURATION_ERROR)

    return log_level


def build_configuration_rpms_from(repository, revision):
    try:
        path_to_config = config.get(KEY_SVN_PATH_TO_CONFIG)
        svn_service = SvnService(base_url=repository, path_to_config=path_to_config)
        ConfigRpmMaker(revision=revision, svn_service=svn_service).build()  # first use case is post-commit hook. repo dir can be used as file:/// SVN URL

    except BaseConfigRpmMakerException as e:
        for line in str(e).split("\n"):
            LOGGER.error(line)
        return exit_program('An exception occurred!', return_code=RETURN_CODE_EXCEPTION_OCCURRED)

    except Exception:
        traceback.print_exc(5)
        return exit_program('An unknown exception occurred!', return_code=RETURN_CODE_UNKOWN_EXCEPTION_OCCURRED)

    exit_program(MESSAGE_SUCCESS, return_code=RETURN_CODE_SUCCESS)


def ensure_valid_revision(revision):
    """ Ensures that the given argument is a valid revision and exits the program if not """

    if not revision.isdigit():
        exit_program('Given revision "%s" is not an integer.' % revision, return_code=RETURN_CODE_REVISION_IS_NOT_AN_INTEGER)

    LOGGER.debug('Accepting "%s" as a valid subversion revision.', revision)
    return revision


def ensure_valid_repository_url(repository_url):
    """ Ensures that the given url is a valid repository url """

    parsed_url = urlparse(repository_url)
    scheme = parsed_url.scheme

    if scheme in VALID_REPOSITORY_URL_SCHEMES:
        LOGGER.debug('Accepting "%s" as a valid repository url.', repository_url)
        return repository_url

    if scheme is '':
        file_uri = 'file://%s' % parsed_url.path
        LOGGER.debug('Accepting "%s" as a valid repository url.', file_uri)
        return file_uri

    return exit_program('Given repository url "%s" is invalid.' % repository_url, return_code=RETURN_CODE_REPOSITORY_URL_INVALID)


def append_console_logger(logger, console_log_level):
    """ Creates and appends a console log handler with the given log level """
    console_handler = create_console_handler(console_log_level)
    logger.addHandler(console_handler)

    if console_log_level == DEBUG:
        logger.debug("DEBUG logging is enabled")


def apply_arguments_to_config(arguments):
    config.setvalue(KEY_RPM_UPLOAD_CMD, arguments[KEY_RPM_UPLOAD_CMD])
    config.setvalue(KEY_CONFIG_VIEWER_ONLY, arguments[KEY_CONFIG_VIEWER_ONLY])


def main():
    LOGGER.setLevel(DEBUG)

    config.load_configuration_file()

    arguments = parse_arguments(argv[1:], version='yadt-config-rpm-maker 2.0')
    apply_arguments_to_config(arguments)

    console_log_level = determine_console_log_level(arguments)
    append_console_logger(LOGGER, console_log_level)

    repository_url = ensure_valid_repository_url(arguments[ARGUMENT_REPOSITORY])
    revision = ensure_valid_revision(arguments[ARGUMENT_REVISION])

    if not arguments[OPTION_NO_SYSLOG]:
        sys_log_handler = create_sys_log_handler(revision)
        LOGGER.addHandler(sys_log_handler)

    start_measuring_time()
    log_process_id(LOGGER.info)
    log_configuration(LOGGER.debug, config.configuration, config.configuration_file_path)

    build_configuration_rpms_from(repository_url, revision)
