# coding=utf-8
#
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

from unittest import TestCase

from mock import Mock, call, patch

from config_rpm_maker import (extract_repository_url_and_revision_from_arguments,
                              initialize_configuration,
                              initialize_logging_to_console,
                              initialize_logging_to_syslog,
                              main,
                              building_configuration_rpms_and_clean_host_directories)
from config_rpm_maker.exceptions import BaseConfigRpmMakerException
from config_rpm_maker.configuration import ConfigurationException


class MainTests(TestCase):

    @patch('config_rpm_maker.building_configuration_rpms_and_clean_host_directories')
    @patch('config_rpm_maker.log_additional_information')
    @patch('config_rpm_maker.start_measuring_time')
    @patch('config_rpm_maker.initialize_logging_to_syslog')
    @patch('config_rpm_maker.extract_repository_url_and_revision_from_arguments')
    @patch('config_rpm_maker.initialize_logging_to_console')
    @patch('config_rpm_maker.initialize_configuration')
    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    def test_should_return_with_success_message_and_return_code_zero_when_everything_works_as_expected(self, mock_exit_program, mock_parse_arguments, mock_initialize_configuration, mock_initialize_logging_to_console, mock_extract_repository_url_and_revision_from_arguments, mock_initialize_logging_to_syslog, mock_start_measuring_time, mock_log_additional_information, mock_start_building_configuration_rpms):

        mock_extract_repository_url_and_revision_from_arguments.return_value = ('repository-url', '123')

        main()

        mock_exit_program.assert_called_with("Success.", return_code=0)

    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    def test_should_return_with_error_message_and_error_code_when_exception_occurrs(self, mock_exit_program, mock_parse_arguments):

        mock_parse_arguments.side_effect = BaseConfigRpmMakerException("We knew this could happen!")

        main()

        mock_exit_program.assert_called_with('An exception occurred!', return_code=4)

    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    def test_should_return_with_error_message_and_error_code_when_configuration_exception_occurrs(self, mock_exit_program, mock_parse_arguments):

        mock_parse_arguments.side_effect = ConfigurationException("We knew this could happen!")

        main()

        mock_exit_program.assert_called_with('Configuration error!', return_code=3)

    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    def test_should_return_with_error_message_and_error_code_when_user_interrupts_execution(self, mock_exit_program, mock_parse_arguments):

        mock_parse_arguments.side_effect = KeyboardInterrupt()

        main()

        mock_exit_program.assert_called_with('Execution interrupted by user!', return_code=7)

    @patch('config_rpm_maker.LOGGER')
    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.traceback')
    def test_should_print_traceback_when_completly_unexpected_exception_occurrs(self, mock_traceback, mock_exit_program, mock_parse_arguments, mock_logger):

        mock_traceback.format_exc.return_value = 'stacktrace line1\nline2\nline3\n'
        mock_parse_arguments.side_effect = Exception("WTF!")

        main()

        mock_traceback.format_exc.assert_called_with(5)
        self.assertEqual([call('stacktrace line1'),
                          call('line2'),
                          call('line3'),
                          call('')],
                         mock_logger.error.call_args_list)

    @patch('config_rpm_maker.parse_arguments')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.traceback')
    def test_should_return_with_error_message_and_error_code_when_completly_unexpected_exception_occurrs(self, mock_traceback, mock_exit_program, mock_parse_arguments):

        mock_parse_arguments.side_effect = Exception("WTF!")

        main()

        mock_exit_program.assert_called_with('An unknown exception occurred!', return_code=5)


class BuildingConfigurationRpmsAndCleanHostDirectoriesTests(TestCase):

    @patch('config_rpm_maker.clean_up_deleted_hosts_data')
    @patch('config_rpm_maker.get_svn_path_to_config')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.SvnService')
    @patch('config_rpm_maker.ConfigRpmMaker')
    def test_should_pass_when_everything_works_as_expected(self, mock_config_rpm_maker_class, mock_svn_service_class, mock_exit_program, mock_config, mock_clean_up_deleted_hosts_data):

        mock_config.return_value = '/path-to-configuration'
        mock_svn_service_class.return_value = Mock()
        mock_config_rpm_maker_class.return_value = Mock()

        building_configuration_rpms_and_clean_host_directories('file:///path_to/testdata/repository', 1)

    @patch('config_rpm_maker.clean_up_deleted_hosts_data')
    @patch('config_rpm_maker.get_svn_path_to_config')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.SvnService')
    @patch('config_rpm_maker.ConfigRpmMaker')
    def test_should_initialize_svn_service_with_given_repository_url(self, mock_config_rpm_maker_class, mock_svn_service_constructor, mock_exit_program, mock_config, mock_clean_up_deleted_hosts_data):

        mock_config.return_value = '/path-to-configuration'
        mock_svn_service_constructor.return_value = Mock()
        mock_config_rpm_maker_class.return_value = Mock()

        building_configuration_rpms_and_clean_host_directories('file:///path_to/testdata/repository', 1)

        mock_svn_service_constructor.assert_called_with(path_to_config='/path-to-configuration',
                                                        base_url='file:///path_to/testdata/repository')

    @patch('config_rpm_maker.clean_up_deleted_hosts_data')
    @patch('config_rpm_maker.get_svn_path_to_config')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.SvnService')
    @patch('config_rpm_maker.ConfigRpmMaker')
    def test_should_initialize_svn_service_with_path_to_config_from_configuration(self, mock_config_rpm_maker_class, mock_svn_service_constructor, mock_exit_program, mock_config, mock_clean_up_deleted_hosts_data):

        mock_config.return_value = '/path-to-configuration'
        mock_svn_service_constructor.return_value = Mock()
        mock_config_rpm_maker_class.return_value = Mock()

        building_configuration_rpms_and_clean_host_directories('file:///path_to/testdata/repository', 1)

        mock_svn_service_constructor.assert_called_with(path_to_config='/path-to-configuration',
                                                        base_url='file:///path_to/testdata/repository')

    @patch('config_rpm_maker.clean_up_deleted_hosts_data')
    @patch('config_rpm_maker.get_svn_path_to_config')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.SvnService')
    @patch('config_rpm_maker.ConfigRpmMaker')
    def test_should_initialize_config_rpm_maker_with_given_revision_and_svn_service(self, mock_config_rpm_maker_class, mock_svn_service_constructor, mock_exit_program, mock_config, mock_clean_up_deleted_hosts_data):

        mock_config.return_value = '/path-to-configuration'
        mock_svn_service = Mock()
        mock_svn_service_constructor.return_value = mock_svn_service
        mock_config_rpm_maker_class.return_value = Mock()

        building_configuration_rpms_and_clean_host_directories('file:///path_to/testdata/repository', '1980')

        mock_config_rpm_maker_class.assert_called_with(svn_service=mock_svn_service, revision='1980')

    @patch('config_rpm_maker.clean_up_deleted_hosts_data')
    @patch('config_rpm_maker.get_svn_path_to_config')
    @patch('config_rpm_maker.exit_program')
    @patch('config_rpm_maker.SvnService')
    @patch('config_rpm_maker.ConfigRpmMaker')
    def test_should_clean_up_directories_of_hosts_which_have_been_deleted(self, mock_config_rpm_maker_class, mock_svn_service_constructor, mock_exit_program, mock_config, mock_clean_up_deleted_hosts_data):

        mock_config.return_value = '/path-to-configuration'
        mock_svn_service = Mock()
        mock_svn_service_constructor.return_value = mock_svn_service
        mock_config_rpm_maker_class.return_value = Mock()

        building_configuration_rpms_and_clean_host_directories('file:///path_to/testdata/repository', '1980')

        mock_clean_up_deleted_hosts_data.assert_called_with(mock_svn_service, '1980')


class InitializeLoggingToConsoleTests(TestCase):

    @patch('config_rpm_maker.LOGGER')
    @patch('config_rpm_maker.append_console_logger')
    @patch('config_rpm_maker.determine_console_log_level')
    def test_should_determine_log_level_using_arguments_and_append_handler_to_root_logger(self, mock_determine_console_log_level, mock_append_console_logger, mock_root_logger):

        mock_arguments = Mock()
        mock_determine_console_log_level.return_value = 'log-level'

        initialize_logging_to_console(mock_arguments)

        mock_determine_console_log_level.assert_called_with(mock_arguments)
        mock_append_console_logger.assert_called_with(mock_root_logger, 'log-level')


class InitializeConfigurationTest(TestCase):

    @patch('config_rpm_maker.apply_arguments_to_config')
    @patch('config_rpm_maker.load_configuration_file')
    def test_should_load_configuration_file(self, mock_load_configuration_file, mock_apply_arguments_to_config):

        mock_arguments = Mock()

        initialize_configuration(mock_arguments)

        mock_load_configuration_file.assert_called_with()

    @patch('config_rpm_maker.apply_arguments_to_config')
    @patch('config_rpm_maker.load_configuration_file')
    def test_should_apply_arguments_to_configuration(self, mock_load_configuration_file, mock_apply_arguments_to_config):

        mock_arguments = Mock()

        initialize_configuration(mock_arguments)

        mock_apply_arguments_to_config.assert_called_with(mock_arguments)


class ExtractRepositoryUrlAndRevisionFromArgumentsTests(TestCase):

    @patch('config_rpm_maker.ensure_valid_repository_url')
    @patch('config_rpm_maker.ensure_valid_revision')
    def test_should_ensure_repository_url_is_valid_before_returning_it(self, mock_ensure_valid_revision, mock_ensure_valid_repository_url):

        mock_ensure_valid_repository_url.return_value = 'valid repository URL'

        actual_repository_url, _ = extract_repository_url_and_revision_from_arguments({'<repository-url>': 'given repository URL', '<revision>': '123'})

        mock_ensure_valid_repository_url.assert_called_with('given repository URL')
        self.assertEqual('valid repository URL', actual_repository_url)

    @patch('config_rpm_maker.ensure_valid_repository_url')
    @patch('config_rpm_maker.ensure_valid_revision')
    def test_should_ensure_revision_is_valid_before_returning_it(self, mock_ensure_valid_revision, mock_ensure_valid_repository_url):

        mock_ensure_valid_revision.return_value = 'valid revision'

        _, actual_revision = extract_repository_url_and_revision_from_arguments({'<repository-url>': 'given repository URL', '<revision>': '123'})

        mock_ensure_valid_revision.assert_called_with('123')
        self.assertEqual('valid revision', actual_revision)


class InitializeLoggingToSysLogTests(TestCase):

    @patch('config_rpm_maker.LOGGER')
    @patch('config_rpm_maker.create_sys_log_handler')
    def test_should_initialize_sys_log_handler_with_given_revision_when_optin_not_given(self, mock_create_sys_log_handler, mock_logger):

        mock_handler = Mock()
        mock_create_sys_log_handler.return_value = mock_handler

        initialize_logging_to_syslog({'--no-syslog': False}, '23784')

        mock_create_sys_log_handler.assert_called_with('23784')
        mock_logger.addHandler.assert_called_with(mock_handler)

    @patch('config_rpm_maker.LOGGER')
    @patch('config_rpm_maker.create_sys_log_handler')
    def test_should_not_initialize_sys_log_handler_when_optin_is_given(self, mock_create_sys_log_handler, mock_logger):

        mock_handler = Mock()
        mock_create_sys_log_handler.return_value = mock_handler

        initialize_logging_to_syslog({'--no-syslog': True}, '23784')

        self.assertEqual(0, mock_create_sys_log_handler.call_count)
        self.assertEqual(0, mock_logger.addHandler.call_count)
