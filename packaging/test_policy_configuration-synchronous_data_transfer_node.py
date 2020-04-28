import os
import sys
import shutil
import contextlib
import tempfile
import json
import os.path

from time import sleep

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

from ..configuration import IrodsConfig
from ..controller import IrodsController
from .resource_suite import ResourceBase
from ..test.command import assert_command
from . import session
from .. import test
from .. import paths
from .. import lib
import ustrings



@contextlib.contextmanager
def event_handler_configured(arg=None):
    filename = paths.server_config_path()
    with lib.file_backed_up(filename):
        irods_config = IrodsConfig()
        irods_config.server_config['advanced_settings']['rule_engine_server_sleep_time_in_seconds'] = 1

        irods_config.server_config['plugin_configuration']['rule_engines'].insert(0,
            {
                "instance_name": "irods_rule_engine_plugin-event_handler-data_object_modified-instance",
                "plugin_name": "irods_rule_engine_plugin-event_handler-data_object_modified",
                'plugin_specific_configuration': {
                    "policies_to_invoke" : [
                        {
                            "conditional" : {
                                "logical_path" : "\/tempZone.*"
                            },
                            "active_policy_clauses" : ["post"],
                            "events" : ["put"],
                            "policy"    : "irods_policy_data_replication",
                            "configuration" : {
                                "source_to_destination_map" : {
                                    "demoResc" : ["AnotherResc"]
                                }
                            }
                        },
                        {
                            "conditional" : {
                                "logical_path" : "\/tempZone.*",
                                "source_resource" : "demoResc"
                            },
                            "active_policy_clauses" : ["post"],
                            "events" : ["replication"],
                            "policy"    : "irods_policy_data_retention",
                            "configuration" : {
                            }
                        },
                        {
                            "conditional" : {
                                "logical_path" : "\/tempZone.*"
                            },
                            "active_policy_clauses" : ["pre"],
                            "events" : ["get"],
                            "policy"    : "irods_policy_data_replication",
                            "configuration" : {
                                "source_to_destination_map" : {
                                    "AnotherResc" : ["demoResc"]
                                }
                            }
                        }
                    ]
                }
            }
        )

        irods_config.server_config['plugin_configuration']['rule_engines'].insert(0,
           {
                "instance_name": "irods_rule_engine_plugin-policy_engine-data_replication-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-data_replication",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
           }
        )

        irods_config.server_config['plugin_configuration']['rule_engines'].insert(0,
           {
                "instance_name": "irods_rule_engine_plugin-policy_engine-data_retention-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-data_retention",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
           }
        )

        irods_config.server_config['plugin_configuration']['rule_engines'].insert(0,
           {
                "instance_name": "irods_rule_engine_plugin-policy_engine-data_retention-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-data_retention",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
           }
        )

        irods_config.commit(irods_config.server_config, irods_config.server_config_path)

        IrodsController().restart()

        try:
            yield
        finally:
            pass


class TestPolicyConfigurationDTN(ResourceBase, unittest.TestCase):
    def setUp(self):
        super(TestPolicyConfigurationDTN, self).setUp()

    def tearDown(self):
        super(TestPolicyConfigurationDTN, self).tearDown()

    def test_event_handler_put(self):
        with session.make_session_for_existing_admin() as admin_session:
            with event_handler_configured():
                try:
                    filename = 'test_put_file'
                    lib.create_local_testfile(filename)
                    admin_session.assert_icommand('iput ' + filename)
                    admin_session.assert_icommand('ils -l ' + filename, 'STDOUT_SINGLELINE', 'AnotherResc')
                finally:
                    admin_session.assert_icommand('irm -f ' + filename)


    def test_event_handler_get(self):
        with session.make_session_for_existing_admin() as admin_session:
            filename = 'test_put_file'
            lib.create_local_testfile(filename)
            with event_handler_configured():
                try:
                    admin_session.assert_icommand('iput ' + filename)
                    admin_session.assert_icommand('ils -l ' + filename, 'STDOUT_SINGLELINE', 'AnotherResc')
                    admin_session.assert_icommand('iget -R AnotherResc -f ' + filename)
                    admin_session.assert_icommand('ils -l ' + filename, 'STDOUT_SINGLELINE', 'demoResc')
                    admin_session.assert_icommand('ils -l ' + filename, 'STDOUT_SINGLELINE', 'AnotherResc')
                finally:
                    admin_session.assert_icommand('irm -f ' + filename)



