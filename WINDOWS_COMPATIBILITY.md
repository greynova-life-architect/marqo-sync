# Windows Compatibility Guide

## Issue Description

The codebase indexer was experiencing errors on Windows systems:
```
'handle' must be a _ThreadHandle
```

This error occurs with `watchdog==3.0.0` on Windows due to thread handle compatibility issues.

## Solutions Implemented

### 1. Downgraded Watchdog Version

Changed `requirements.txt` from:
```
watchdog==3.0.0
```
to:
```
watchdog==2.3.1
```

Version 2.3.1 is more stable on Windows and doesn't have the thread handle issues.

### 2. Added Windows-Specific Fallback

The watcher now automatically detects Windows systems and falls back to `PollingObserver` if the default `Observer` fails.

### 3. Environment Variable Control

You can force the use of `PollingObserver` on Windows by setting:
```bash
set WATCHDOG_USE_POLLING=1
```

Or in PowerShell:
```powershell
$env:WATCHDOG_USE_POLLING=1
```

## How It Works

1. **Automatic Detection**: The system detects Windows and tries the default observer first
2. **Fallback**: If the default observer fails, it automatically switches to `PollingObserver`
3. **Manual Override**: You can force `PollingObserver` using the environment variable

## PollingObserver vs Observer

- **Observer**: Uses native file system events (faster, more efficient)
- **PollingObserver**: Polls for changes at regular intervals (more compatible, slightly slower)

## Testing

Run the test script to verify compatibility:
```bash
python test_watcher.py
```

## Troubleshooting

If you still experience issues:

1. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Force polling observer**:
   ```bash
   set WATCHDOG_USE_POLLING=1
   python -m src.sync.main_enhanced
   ```

3. **Check logs**: Look for specific error messages in the logs

## Performance Considerations

- `PollingObserver` uses more CPU but is more reliable on Windows
- The polling interval can be adjusted if needed
- For production use, consider using the default observer if it works on your system
