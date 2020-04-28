set(POLICY_NAME "synchronous_data_transfer_node")


string(REPLACE "_" "-" POLICY_NAME_HYPHENS ${POLICY_NAME})
set(IRODS_PACKAGE_COMPONENT_POLICY_NAME "${POLICY_NAME_HYPHENS}${IRODS_PACKAGE_FILE_NAME_SUFFIX}")
string(TOUPPER ${IRODS_PACKAGE_COMPONENT_POLICY_NAME} IRODS_PACKAGE_COMPONENT_POLICY_NAME_UPPERCASE)

set(TARGET_NAME "${PROJECT_NAME}-policy_configuration-${POLICY_NAME}")
string(REPLACE "_" "-" TARGET_NAME_HYPHENS ${TARGET_NAME})

install(
  FILES
  packaging/test_policy_configuration-${POLICY_NAME}.py
  DESTINATION var/lib/irods/scripts/irods/test
  COMPONENT ${IRODS_PACKAGE_COMPONENT_POLICY_NAME}
  )

set(CPACK_PACKAGE_VERSION ${IRODS_PLUGIN_VERSION})
set(CPACK_DEBIAN_${IRODS_PACKAGE_COMPONENT_POLICY_NAME_UPPERCASE}_FILE_NAME ${TARGET_NAME_HYPHENS}-${IRODS_PLUGIN_VERSION}-${IRODS_LINUX_DISTRIBUTION_NAME}-${IRODS_LINUX_DISTRIBUTION_VERSION_MAJOR}-${CMAKE_SYSTEM_PROCESSOR}.deb)


set(CPACK_DEBIAN_${IRODS_PACKAGE_COMPONENT_POLICY_NAME_UPPERCASE}_PACKAGE_NAME ${TARGET_NAME_HYPHENS})
set(CPACK_DEBIAN_${IRODS_PACKAGE_COMPONENT_POLICY_NAME_UPPERCASE}_PACKAGE_DEPENDS "${IRODS_PACKAGE_DEPENDENCIES_STRING}, irods-server (= ${IRODS_VERSION}), irods-runtime (= ${IRODS_VERSION}), libc6, irods-rule-engine-plugin-policy-engine-data-replication, irods-rule-engine-plugin-policy-engine-data-verification, irods-rule-engine-plugin-policy-engine-data-retention")

set(CPACK_RPM_${IRODS_PACKAGE_COMPONENT_POLICY_NAME}_PACKAGE_NAME ${TARGET_NAME_HYPHENS})
if (IRODS_LINUX_DISTRIBUTION_NAME STREQUAL "centos" OR IRODS_LINUX_DISTRIBUTION_NAME STREQUAL "centos linux")
    set(CPACK_RPM_${IRODS_PACKAGE_COMPONENT_POLICY_NAME_UPPERCASE}_FILE_NAME ${TARGET_NAME_HYPHENS}-${IRODS_PLUGIN_VERSION}-${IRODS_LINUX_DISTRIBUTION_NAME}-${IRODS_LINUX_DISTRIBUTION_VERSION_MAJOR}-${CMAKE_SYSTEM_PROCESSOR}.deb)
    set(CPACK_RPM_${IRODS_PACKAGE_COMPONENT_POLICY_NAME}_PACKAGE_REQUIRES "${IRODS_PACKAGE_DEPENDENCIES_STRING}, irods-server = ${IRODS_VERSION}, irods-runtime = ${IRODS_VERSION}, openssl, irods-rule-engine-plugin-policy-engine-data-replication, irods-rule-engine-plugin-policy-engine-data-verification, irods-rule-engine-plugin-policy-engine-data-retention")
elseif (IRODS_LINUX_DISTRIBUTION_NAME STREQUAL "opensuse")
    set(CPACK_RPM_${IRODS_PACKAGE_COMPONENT_POLICY_NAME}_PACKAGE_REQUIRES "${IRODS_PACKAGE_DEPENDENCIES_STRING}, irods-server = ${IRODS_VERSION}, irods-runtime = ${IRODS_VERSION}, libopenssl1_0_0, irods-rule-engine-plugin-policy-engine-data-replication, irods-rule-engine-plugin-policy-engine-data-verification, irods-rule-engine-plugin-policy-engine-data-retention")
endif()

