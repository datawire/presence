# Datawire Presence

Presence is a Python program that performs runtime environment information discovery.

# Configuration

Presence looks for configuration in `/etc/datawire/presence.yml`

```yaml
---
type: <ec2|custom>
```

## Supported Environments

1. ec2
2. docker
3. custom (see: Custom Environment Plugin)

# Custom Environment Information Plugin

Environments can be unique and it is not possible for Presence to support every known configuration. 


A custom presence plugin allows developers to implement custom network discovery logic.

# License

Apache 2.0