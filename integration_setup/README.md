# Integration Setup Scripts

Collection of scripts that install integrations.

## Zabbix Setup

A script that does all the configuration of a Zabbix server for integrating with PagerDuty in an automated fashion. It has been built and tested with Zabbix 4.

If you can connect to the Zabbix server's API / web UI, you can run this script. You'll need the following:

* A Zabbix username / password for a user account that has administrator-level permissions.
* A PagerDuty integration key.

**What it does:** all of the tasks that you would otherwise need to perform by hand in the Zabbix UI.

**What it does not do,** that you will need to do separately in order to complete the integration:

* [Install PagerDuty Agent](https://www.pagerduty.com/docs/guides/agent-install-guide/) and the `pdagent-integrations` package.
* Make a symbolic link to the `pd-zabbix` script (from the `pdagent-integrations` package) in the appropriate `AlertScriptsPath` directory as configured on your own Zabbix server.

For more details, refer to the [Zabbix Integration Guide](https://www.pagerduty.com/docs/guides/zabbix-3-integration-guide/).
