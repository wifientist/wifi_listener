# Database Migration Guide

## Migrating Existing Database

If you have an existing `wifi_metrics.db` from before the iperf3 feature was added, you need to run a migration to add the new columns.

### Run Migration

```bash
python3 migrate_add_iperf3.py
```

This will:
- Add iperf3-related columns to the sessions table
- Preserve all existing data
- Set iperf3_enabled=0 (false) for all existing sessions
- Be safe to run multiple times (idempotent)

### What Gets Added

New columns in `sessions` table:
- `iperf3_enabled` - Boolean flag
- `iperf3_server` - Server IP/hostname
- `iperf3_port` - Server port
- `iperf3_parallel` - Number of parallel streams
- `iperf3_reverse` - Reverse mode flag
- `iperf3_udp` - UDP mode flag

### If You're Starting Fresh

No migration needed! Just delete the old database and it will be recreated with the new schema:

```bash
rm data/wifi_metrics.db
python3 wifi_listener.py start -l "Test" -a "AP1" -d 1
# Ctrl+C to stop
```

### Troubleshooting

**"no such column: iperf3_enabled"**
- You need to run the migration
- Or delete and recreate the database

**Migration fails**
- Check database isn't locked
- Make sure no sessions are actively running
- Check file permissions on data/ directory

### Future Migrations

As new features are added, migration scripts will be provided in the root directory named:
- `migrate_add_iperf3.py` - Adds iperf3 columns (current)
- `migrate_xxx.py` - Future migrations
