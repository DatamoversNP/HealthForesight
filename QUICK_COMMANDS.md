# Quick Commands - Run from Anywhere

## From `apps/api` directory:

### Check Status:
```bash
cd scripts && ./check_status.sh
```

Or use the shortcut:
```bash
./QUICK_STATUS.sh
```

### Check & Create Observations:
```bash
python3 scripts/check_and_create_observations.py
```

### Watch Monitor Log:
```bash
tail -f /tmp/observation_monitor.log
```

### Start Monitor:
```bash
cd scripts && ./start_observation_monitor.sh
```

### Stop Monitor:
```bash
cd scripts && ./stop_observation_monitor.sh
```

---

## From Project Root:

### Check Status:
```bash
cd apps/api/scripts && ./check_status.sh
```

### Check & Create Observations:
```bash
cd apps/api && python3 scripts/check_and_create_observations.py
```

---

## Simplest Commands (from `apps/api`):

```bash
# Status check
cd scripts && ./check_status.sh

# Or use shortcut
./QUICK_STATUS.sh

# Manual check & create
python3 scripts/check_and_create_observations.py

# Watch monitor
tail -f /tmp/observation_monitor.log
```
