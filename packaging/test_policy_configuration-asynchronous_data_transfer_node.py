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
                            "events" : ["put", "get"],
                            "policy_to_invoke"    : "irods_policy_access_time",
                            "configuration" : {
                                "source_to_destination_map" : {
                                    "demoResc" : ["AnotherResc"]
                                }
                            }
                        },
                        {
                            "conditional" : {
                                "logical_path" : "\/tempZone.*"
                            },
                            "active_policy_clauses" : ["post"],
                            "events" : ["put"],
                            "policy_to_invoke"    : "irods_policy_data_replication",
                            "configuration" : {
                                "source_to_destination_map" : {
                                    "demoResc" : ["AnotherResc"]
                                }
                            }
                        },
                        {
                            "conditional" : {
                                "logical_path" : "\/tempZone.*"
                            },
                            "active_policy_clauses" : ["pre"],
                            "events" : ["get"],
                            "policy_to_invoke"    : "irods_policy_data_replication",
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
                "instance_name": "irods_rule_engine_plugin-policy_engine-access_time-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-access_time",
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

def wait_for_empty_queue(function):
    done = False
    while done == False:
        out, err, rc = lib.execute_command_permissive(['iqstat', '-a'])
        if -1 != out.find('No delayed rules pending'):
            try:
                function()
            except:
                pass
            done = True
        else:
            print('    Output ['+out+']')
            sleep(1)

retention_rule = """
{
        "policy" : "irods_policy_enqueue_rule",
        "delay_conditions" : "<PLUSET>1s</PLUSET>",
        "payload" : {
            "policy" : "irods_policy_execute_rule",
            "payload" : {
                "policy_to_invoke" : "irods_policy_query_processor",
                "lifetime" : "2",
                "parameters" : {
                    "query_string" : "SELECT USER_NAME, COLL_NAME, DATA_NAME, RESC_NAME WHERE COLL_NAME like '/tempZone/home/rods%' AND META_DATA_ATTR_NAME = 'irods::access_time' AND META_DATA_ATTR_VALUE < 'IRODS_TOKEN_LIFETIME' AND RESC_NAME = 'demoResc",
                    "query_limit" : 10,
                    "query_type" : "general",
                    "number_of_threads" : 1,
                    "policy_to_invoke" : "irods_policy_data_retention"
                 },
                 "configuration" : {
                     "mode" : "trim_single_replica"
                 }
             }
        }
}
INPUT null
OUTPUT ruleExecOut
"""

demo_resc_query = """ iquest "SELECT DATA_ID WHERE DATA_NAME = 'test_put_file' AND RESC_NAME = 'demoResc'" """

class TestPolicyConfigurationDTN(ResourceBase, unittest.TestCase):
    def setUp(self):
        super(TestPolicyConfigurationDTN, self).setUp()
        with open('example_retention_rule.r', 'w') as f:
            f.write(retention_rule)

    def tearDown(self):
        super(TestPolicyConfigurationDTN, self).tearDown()
        os.remove('example_retention_rule.r')

    def test_event_handler_put(self):
        with session.make_session_for_existing_admin() as admin_session:
            with event_handler_configured():
                try:
                    filename = 'test_put_file'
                    lib.create_local_testfile(filename)
                    admin_session.assert_icommand('iput ' + filename)
                    admin_session.assert_icommand('ils -l ' + filename, 'STDOUT_SINGLELINE', 'AnotherResc')
                    admin_session.assert_icommand('irule -F example_retention_rule.r')
                    wait_for_empty_queue(lambda: alice_session.assert_icommand(demo_resc_query, 'STDOUT_SINGLE_LINE', 'CAT_NO_ROWS_FOUND'))
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
                    admin_session.assert_icommand('irule -F example_retention_rule.r')
                    wait_for_empty_queue(lambda: alice_session.assert_icommand(demo_resc_query, 'STDOUT_SINGLE_LINE', 'CAT_NO_ROWS_FOUND'))
                finally:
                    admin_session.assert_icommand('irm -f ' + filename)



