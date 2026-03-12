# Router SNMP Monitoring — Future Enhancement

Current router monitoring uses ping + SSH script polling (see Router model).
This document describes a full SNMP-based upgrade for OpenWrt routers.

## When to implement
- When per-interface traffic graphs are needed
- When SSH access to the router is not practical
- When more structured metrics (load, memory) are needed without custom scripts

## Architecture

### New models (separate from Router)
- `RouterMetric`: uptime_seconds, load_1/5/15, mem_total_kb, mem_free_kb, recorded_at
- `RouterInterface`: if_index, if_name, if_descr, if_oper_status, bytes_in, bytes_out, updated_at

### Dependency
```
puresnmp==2.3.0  # pure Python, no C deps
```

### OIDs to poll
| OID | Description |
|-----|-------------|
| `1.3.6.1.2.1.1.3.0` | sysUpTime (hundredths of seconds) |
| `1.3.6.1.4.1.2021.10.1.3.1` | UCD laLoad.1 (1-min load avg string) |
| `1.3.6.1.4.1.2021.10.1.3.2` | UCD laLoad.2 (5-min load avg) |
| `1.3.6.1.4.1.2021.10.1.3.3` | UCD laLoad.3 (15-min load avg) |
| `1.3.6.1.4.1.2021.4.5.0` | memTotalReal (kB) |
| `1.3.6.1.4.1.2021.4.6.0` | memAvailReal (kB) |
| `1.3.6.1.2.1.2.2.1.*` | ifTable (index, descr, status, octets) |
| `1.3.6.1.2.1.31.1.1.1.1.*` | ifName (from ifXTable) |
| `1.3.6.1.2.1.31.1.1.1.6.*` | ifHCInOctets (64-bit in) |
| `1.3.6.1.2.1.31.1.1.1.10.*` | ifHCOutOctets (64-bit out) |

### Router model additions
```python
snmp_community = Column(String(100), default="public")
snmp_port = Column(Integer, default=161)
snmp_version = Column(String(10), default="2c")  # "1" or "2c"
use_snmp = Column(Boolean, default=False)  # if False, use existing SSH+ping
```

### Polling function (sync, run via run_in_executor in scheduler)
```python
import puresnmp

def poll_router_snmp(host, community, port=161):
    oids = [
        '1.3.6.1.2.1.1.3.0',
        '1.3.6.1.4.1.2021.10.1.3.1',
        '1.3.6.1.4.1.2021.10.1.3.2',
        '1.3.6.1.4.1.2021.10.1.3.3',
        '1.3.6.1.4.1.2021.4.5.0',
        '1.3.6.1.4.1.2021.4.6.0',
    ]
    values = puresnmp.multiget(host, community, oids, port=port)
    uptime_centiseconds = int(values[0])
    load_1  = float(values[1])
    load_5  = float(values[2])
    load_15 = float(values[3])
    mem_total_kb = int(values[4])
    mem_free_kb  = int(values[5])

    # Walk interfaces
    interfaces = []
    if_names    = dict(puresnmp.walk(host, community, '1.3.6.1.2.1.31.1.1.1.1', port=port))
    if_status   = dict(puresnmp.walk(host, community, '1.3.6.1.2.1.2.2.1.8', port=port))
    if_in_hc    = dict(puresnmp.walk(host, community, '1.3.6.1.2.1.31.1.1.1.6', port=port))
    if_out_hc   = dict(puresnmp.walk(host, community, '1.3.6.1.2.1.31.1.1.1.10', port=port))

    for oid, name in if_names.items():
        idx = oid.split('.')[-1]
        status_oid  = f'1.3.6.1.2.1.2.2.1.8.{idx}'
        in_oid      = f'1.3.6.1.2.1.31.1.1.1.6.{idx}'
        out_oid     = f'1.3.6.1.2.1.31.1.1.1.10.{idx}'
        interfaces.append({
            'if_index': int(idx),
            'if_name': str(name),
            'if_oper_status': int(if_status.get(status_oid, 2)),
            'bytes_in': int(if_in_hc.get(in_oid, 0)),
            'bytes_out': int(if_out_hc.get(out_oid, 0)),
        })

    return {
        'uptime_seconds': uptime_centiseconds // 100,
        'load_1': load_1, 'load_5': load_5, 'load_15': load_15,
        'mem_total_kb': mem_total_kb, 'mem_free_kb': mem_free_kb,
        'interfaces': interfaces,
    }
```

### OpenWrt setup (for Setup tab)
```sh
opkg update
opkg install snmpd

# /etc/config/snmpd — minimal config
config agent
    option agentaddress  UDP:161

config com2sec
    option secname   local
    option source    192.168.1.0/24   # restrict to LAN
    option community public

config group
    option name     localgroup
    option version  v2c
    option secname  local

config view
    option name     all
    option type     included
    option subtree  .1

config access
    option group    localgroup
    option context  ""
    option version  any
    option level    noauth
    option prefix   exact
    option read     all
    option write    none
    option notify   none

/etc/init.d/snmpd enable
/etc/init.d/snmpd start
```

### New frontend tabs for SNMP mode
- **Overview**: uptime, load gauges (1/5/15), memory bar
- **Interfaces**: table with status, bytes in/out, calculated throughput
- **Metrics**: historical load + memory charts (same pattern as server Metrics tab)
