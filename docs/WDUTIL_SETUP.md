# wdutil Setup (Optional Advanced Metrics)

The WiFi Listener can use Apple's `wdutil` tool to capture additional WiFi metrics beyond what `system_profiler` provides. This is **optional** - the tool works fine without it.

## What wdutil Provides

### Additional Metrics:
- **BSSID** - Reliable AP MAC address capture
- **CCA (Channel Clear Assessment)** - Channel utilization % (how busy the channel is)
- **NSS (Number of Spatial Streams)** - MIMO configuration (e.g., 2x2, 4x4)
- **Guard Interval** - Short (800ns) or Long (3200ns) - affects throughput

### Why CCA Matters:
CCA shows what percentage of time your WiFi channel is busy:
- **< 20%** = Excellent (clean channel)
- **20-40%** = Good (some activity)
- **40-70%** = Fair (moderate congestion)
- **> 70%** = Poor (heavy interference)

This helps diagnose why you might have good signal but poor throughput!

---

## Requirements

`wdutil` requires **sudo** access. You have two options:

### Option 1: Run Without wdutil (Default)
**No setup needed!** The tool automatically falls back to `system_profiler` and captures:
- Signal, Noise, SNR, TX Rate, MCS, Channel, PHY mode
- iperf3 throughput
- Everything you need for rate@range testing

### Option 2: Enable wdutil (Advanced)
Configure passwordless sudo for `wdutil info` to get the extra metrics.

---

## Setup Instructions (Option 2)

### Step 1: Edit Sudoers File

**⚠️ Warning:** Editing sudoers incorrectly can lock you out of sudo. Always use `visudo`.

```bash
sudo visudo
```

### Step 2: Add wdutil Permission

Add this line at the **end** of the file:

```
yourusername ALL=(ALL) NOPASSWD: /usr/sbin/wdutil info
```

Replace `yourusername` with your actual username. To check your username:
```bash
whoami
```

### Step 3: Save and Exit

- In `vi` editor: Press `Esc`, then type `:wq` and press `Enter`
- `visudo` will validate the syntax before saving

### Step 4: Test It

```bash
sudo -n wdutil info
```

If configured correctly, this should show WiFi info without asking for a password.

---

## Verification

Run a test session:

```bash
python3 wifi_listener.py start -l "test" -a "test" -d 0.1
```

Then check the stats:

```bash
python3 wifi_listener.py stats <session_id>
```

If wdutil is working, you'll see:
```
Connection Details:
  ...
  Spatial Streams: 2x2 MIMO
  Guard Interval: 800ns (Short)
  Channel Utilization: 10% (Excellent)
```

If wdutil is **not** configured, you'll see everything except those three lines.

---

## Security Considerations

### Is This Safe?

**Mostly yes**, with caveats:

✅ **Only allows `wdutil info`** - read-only command, cannot modify system
✅ **Tool itself doesn't run as root** - only the wdutil subprocess does
✅ **No password in code** - relies on sudo configuration

⚠️ **Anyone with your user account** can run `sudo wdutil info`
⚠️ **Managed Macs** may not allow sudoers modifications

### Alternative: Don't Use wdutil

For most users, `system_profiler` provides everything needed:
- Signal strength and quality metrics
- TX rate and MCS index
- iperf3 actual throughput
- Channel and PHY mode

The extra wdutil metrics are "nice to have" for deep troubleshooting, not essential for rate@range testing.

---

## Troubleshooting

### "sudo: a password is required"

wdutil is not configured for passwordless access. The tool will automatically fall back to `system_profiler`.

### "Permission denied" when editing sudoers

You need admin/sudo access to configure this. If you're on a managed/corporate Mac, you may not have permission.

### Still asking for password after setup

1. Check your username matches exactly: `whoami`
2. Verify the path is correct: `which wdutil` should show `/usr/sbin/wdutil`
3. Make sure there are no typos in the sudoers line
4. The line should be at the **end** of the file (after other rules)

### How to remove wdutil access

```bash
sudo visudo
```

Find and delete the line you added, then save.

---

## Summary

- **wdutil is optional** - tool works great without it
- **Provides CCA** - channel utilization metric for diagnosing interference
- **Requires one-time sudo setup** - passwordless access to `wdutil info`
- **Falls back automatically** - no configuration needed if you don't want it

Most users can skip this and use the default `system_profiler` mode! 🎯
