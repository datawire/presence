# Datawire Presence

Presence is a Python program that performs runtime environment information discovery.

# Configuration

Presence looks for configuration in `/etc/datawire/presence.yml`

Example:
```yaml
---
lookup: net(eth0)
watson_plugins:
 - /etc/datawire/watson.yml
```

## Supported Lookups

1. ec2
2. docker
3. custom (see: Custom Environment Plugin)

# Custom Lookup Plugin

Environments can be unique and it is not possible for Presence to support every known configuration. 


A custom presence plugin allows developers to implement custom network discovery logic.

# License

Apache 2.0