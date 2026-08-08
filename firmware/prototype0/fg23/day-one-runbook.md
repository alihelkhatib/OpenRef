# FG23 Day-One Runbook

Use this when the first two `FG23-DK2600A` boards arrive.

## 1. Physical Check

- Confirm both boards are `FG23-DK2600A`.
- Photograph packaging labels for local records.
- Do not commit serial-number photos or personal shipping details.
- Mark boards locally as `node-1` and `node-2`.

## 2. Toolchain Check

- Install Simplicity Studio.
- Install the selected Gecko SDK.
- Connect `node-1`.
- Confirm the board appears in Simplicity Studio.
- Repeat for `node-2`.

Record versions in:

```text
firmware/prototype0/fg23/vendor-notes.md
```

## 3. Serial Port Discovery

From repository root:

```bash
python tools/capture_serial.py --list
```

Record the COM port mapping in local notes. Do not commit machine-specific COM
port assignments as project facts.

## 4. Vendor Example Flash

- Build an unmodified Silicon Labs packet/radio example.
- Flash `node-1`.
- Flash `node-2`.
- Keep the example name and SDK version in `vendor-notes.md`.

## 5. Capture Serial Logs

Example:

```bash
python tools/capture_serial.py \
  --port COM7 \
  --baud 115200 \
  --duration-seconds 120 \
  --output firmware/prototype0/fg23/results/YYYYMMDD-node-1-e0-01.log
```

Run a second terminal for `node-2`.

## 6. Fill E0-01 Result

Copy the template:

```text
firmware/prototype0/fg23/templates/e0-01-toolchain-result.md
```

Save the completed result under local results first. Commit only a summary once
it is free of local serial numbers, screenshots, and machine-specific paths.

## 7. Stop Before Custom Firmware

Do not begin OpenRef packet-pair firmware until:

- both boards flash reliably;
- both boards log over serial;
- the exact vendor example and SDK are recorded;
- E0-01 is complete enough to reproduce.
