# GitHub Setup Instructions

Your local repository is ready to push to GitHub!

## Steps to Publish

### 1. Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `wifi_listener`
3. Description: "macOS WiFi monitoring tool for rate@range testing"
4. **Keep it Public or Private** (your choice)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### 2. Push to GitHub

GitHub will show you commands, but here's what to run:

```bash
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/wifi_listener.git

# Push to GitHub
git push -u origin main
```

### 3. Verify

Open https://github.com/YOUR_USERNAME/wifi_listener in your browser to see your project!

## Future Updates

After making changes:

```bash
git add -A
git commit -m "Description of changes"
git push
```

## Forking for Advanced Version

When you're ready to create the advanced version:

1. On GitHub, click "Fork" on your repo (or create a new repo)
2. Clone the fork locally
3. Add advanced features (RX rate, CoreWLAN, etc.)
4. Keep this version as the "simple" reference

## Current Status

✅ Repository initialized
✅ Initial commit created
✅ .gitignore configured (data/ and exports/ excluded)
✅ README with features and usage
✅ License added (MIT)
✅ Ready to push to GitHub

## Files Included

**Core:**
- `wifi_listener.py` - Main CLI application
- `config.py` - Configuration

**Modules:**
- `db/` - Database layer (SQLite)
- `collectors/` - WiFi data collection
- `exporters/` - CSV and InfluxDB export

**Documentation:**
- `README.md` - Main documentation
- `GRAFANA_SETUP.md` - InfluxDB/Grafana guide
- `LICENSE` - MIT License

**Test Scripts:**
- `test_system_profiler.py` - Test data collection

**Excluded (in .gitignore):**
- `data/` - Your SQLite database
- `exports/` - Your CSV/InfluxDB files
- Python cache files

These are kept local and won't be committed to GitHub.
