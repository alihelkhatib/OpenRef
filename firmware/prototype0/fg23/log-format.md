# Prototype 0 Serial Log Format

Use line-delimited CSV for the first firmware harness. Each line starts with an
event name so mixed logs can be filtered without a binary decoder.

## Common Fields

```text
event,local_time_us,node_id,sequence,result,detail
```

## Events

| Event | Required detail |
|---|---|
| `boot` | firmware build ID and reset reason |
| `radio_init` | frequency, bitrate, TX power, profile ID |
| `tx_queued` | requested TX timestamp and payload length |
| `tx_started` | observed local timestamp |
| `tx_done` | result and packet sequence |
| `rx_done` | sequence, source ID, length, RSSI, LQI, CRC status |
| `rx_gap` | expected sequence and received sequence |
| `fault` | fault bitmap or SDK error code |
| `current_marker` | mode label for aligning current measurements |

## Example

```csv
event,local_time_us,node_id,sequence,result,detail
boot,0,1,0,ok,build=p0-fg23-dev reset=power_on
radio_init,42310,1,0,ok,freq=915000000 bitrate=500000 tx_power=0
tx_queued,100000,1,42,ok,requested_tx_us=105000 length=72
tx_started,105012,1,42,ok,gpio=tx_start
tx_done,106330,1,42,ok,length=72
rx_done,106341,2,42,ok,source=1 length=72 rssi=-44 lqi=220 crc=1
```

## Rules

- Timestamps are local monotonic microseconds.
- Firmware should never log from time-critical vendor interrupt/callback context
  if doing so can disturb radio timing.
- Unknown fields go in `detail` as space-separated `key=value` tokens.
- Binary payloads are not printed in routine logs.
