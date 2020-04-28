# Motivation

Many academic and governmental organizations have mandates to share data with one another. However, most internal networks are not designed for easy sharing with external partners. The common resulting pattern of having a DMZ, or set of machines designated as Data Transfer Nodes, provides a solution to that mandate.  This repository provides the policy configuration to implement a data transfer node using either synchronous or asynchronous data retention by leveraging Policy Composition using an existing body of [Policy Engines](https://github.com/jasoncoposky/irods_rule_engine_plugins_policy).

![One Pager Explanation](https://irods.org/images/pattern_data_transfer_nodes.png)

# Synchronous Data Transfer Node

The configuration of this DTN is designed to synchronously replicate data from the edge to a destination resource configured in the 'source_to_destination_map'.  This map can be configured to replicate data from any given source resource to a list of destination resources.  Should more than one source resource be configured a new key-value entry may be added.  This configuration also provides synchronous data retention after the replication.  The source resource is specified as the condition for the data retention after the replication has been performed.

```json
    "rule_engines": [
        {
            "instance_name": "irods_rule_engine_plugin-event_handler-data_object_modified-instance",
                "plugin_name": "irods_rule_engine_plugin-event_handler-data_object_modified",
                "plugin_specific_configuration": {
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
        },
        {
            "instance_name": "irods_rule_engine_plugin-policy_engine-data_replication-instance",
            "plugin_name": "irods_rule_engine_plugin-policy_engine-data_replication",
            "plugin_specific_configuration": {
                "log_errors" : "true"
            }
        },
        {
            "instance_name": "irods_rule_engine_plugin-policy_engine-data_retention-instance",
            "plugin_name": "irods_rule_engine_plugin-policy_engine-data_retention",
            "plugin_specific_configuration": {
                "log_errors" : "true"
            }
        },
        {
            "instance_name": "irods_rule_engine_plugin-policy_engine-data_retention-instance",
            "plugin_name": "irods_rule_engine_plugin-policy_engine-data_retention",
            "plugin_specific_configuration": {
                "log_errors" : "true"
            }
        }
    ]
```

# Asynchronous Data Transfer Node

The configuration of this DTN is similar to the synchronous example except that this configuration relies on asynchronous data retention.  Data retention is configured as a delayed execution rule that queries for data with an access time of greater than a given age in seconds.

```json
    "rule_engines": [
        {
            "instance_name": "irods_rule_engine_plugin-event_handler-data_object_modified-instance",
                "plugin_name": "irods_rule_engine_plugin-event_handler-data_object_modified",
                "plugin_specific_configuration": {
                    "policies_to_invoke" : [
                    {
                        "conditional" : {
                            "logical_path" : "\/tempZone.*"
                        },
                        "active_policy_clauses" : ["post"],
                        "events" : ["put", "get"],
                        "policy"    : "irods_policy_access_time",
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
                        "policy"    : "irods_policy_data_replication",
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
                        "policy"    : "irods_policy_data_replication",
                        "configuration" : {
                            "source_to_destination_map" : {
                                "AnotherResc" : ["demoResc"]
                            }
                        }
                    }
                    ]
                }
        },
            {
                "instance_name": "irods_rule_engine_plugin-policy_engine-data_replication-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-data_replication",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
            },
            {
                "instance_name": "irods_rule_engine_plugin-policy_engine-data_retention-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-data_retention",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
            },
            {
                "instance_name": "irods_rule_engine_plugin-policy_engine-access_time-instance",
                "plugin_name": "irods_rule_engine_plugin-policy_engine-access_time",
                "plugin_specific_configuration": {
                    "log_errors" : "true"
                }
            }
        ]
```

## Rule for Async Data Retention

This policy composed delayed execution rule is configured to execute a data retention policy for data residing on a given resource which is older than 600 seconds.  This asynchronous rule provides the cache management of Data Transfer Nodes at the edge once data has not been accessed for a sufficient amount of time.

```json
{
        "policy" : "irods_policy_enqueue_rule",
        "delay_conditions" : "<EF>REPEAT FOR EVER</EF>",
        "payload" : {
            "policy" : "irods_policy_execute_rule",
            "payload" : {
                "policy_to_invoke" : "irods_policy_query_processor",
                "lifetime" : "600",
                "parameters" : {
                    "query_string" : "SELECT USER_NAME, COLL_NAME, DATA_NAME, RESC_NAME WHERE COLL_NAME like '/tempZone/home/rods%' AND META_DATA_ATTR_NAME = 'irods::access_time' AND META_DATA_ATTR_VALUE < 'IRODS_TOKEN_LIFETIME' and RESC_NAME = 'demoResc'",
                    "query_limit" : 0,
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
```


