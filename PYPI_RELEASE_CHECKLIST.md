# PyPI Release Checklist for v2.1.0

## Pre-Release Verification

### 1. Version Check
- [x] Version bumped in `token_calculator/__init__.py` (2.0.0 → 2.1.0)
- [ ] Version matches in `setup.py` or `pyproject.toml`

### 2. Code Quality
- [x] All imports working correctly
- [x] No syntax errors
- [x] Message class added and exported
- [x] ConversationMonitor initialization fixed
- [ ] Run tests (if available): `pytest`
- [ ] Check for linting issues: `flake8 token_calculator/`

### 3. Documentation
- [x] README.md updated with new features
- [x] RELEASE_NOTES_v2.1.0.md created
- [x] Examples provided
- [x] Docstrings complete

### 4. Git
- [x] All changes committed
- [x] Changes pushed to GitHub
- [ ] PR created and approved
- [ ] PR merged to main branch

---

## Release Steps

### Step 1: Merge PR to Main

```bash
# After PR approval, merge to main
git checkout main
git pull origin main
```

### Step 2: Tag the Release

```bash
# Create annotated tag
git tag -a v2.1.0 -m "Release v2.1.0 - Production-ready for AI Product Managers"

# Push tag
git push origin v2.1.0
```

### Step 3: Create GitHub Release

1. Go to: https://github.com/arunaryamdn/token-calculator/releases/new
2. Choose tag: v2.1.0
3. Release title: "v2.1.0 - Production-Ready for AI Product Managers"
4. Copy release notes from `RELEASE_NOTES_v2.1.0.md`
5. Mark as "Latest release"
6. Publish release

### Step 4: Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Install/upgrade build tools
pip install --upgrade build twine

# Build distributions
python -m build

# Verify builds
ls -lh dist/
# Should see:
# token_calculator-2.1.0-py3-none-any.whl
# token_calculator-2.1.0.tar.gz
```

### Step 5: Test on TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ token-calculator==2.1.0

# Verify imports
python -c "from token_calculator import CostTracker, WorkflowTracker, ConversationMonitor; print('✅ All imports work!')"
```

### Step 6: Upload to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Enter credentials when prompted
# Username: __token__
# Password: your-pypi-token
```

### Step 7: Verify PyPI Release

```bash
# Wait a few minutes, then install from PyPI
pip uninstall token-calculator -y
pip install token-calculator==2.1.0

# Verify version
python -c "import token_calculator; print(token_calculator.__version__)"
# Should print: 2.1.0

# Test imports
python -c "
from token_calculator import (
    CostTracker,
    WorkflowTracker,
    ConversationMonitor,
    CostForecaster,
    BudgetTracker,
    AlertManager,
    ModelSelector,
    create_storage,
    Message
)
print('✅ All new features available!')
print('✅ Version 2.1.0 successfully published!')
"
```

### Step 8: Update GitHub

1. Update main branch README badge (if version badge exists)
2. Close related issues
3. Announce in Discussions

### Step 9: Announce Release

**GitHub Discussions**:
```
🎉 Token Calculator v2.1.0 Released!

We're excited to announce v2.1.0 - a major release transforming Token Calculator into a production-ready LLM observability platform for AI Product Managers!

🚀 What's New:
- Multi-backend storage (SQLite, PostgreSQL)
- Cost tracking with custom labels
- Multi-agent workflow tracking
- Context health monitoring
- Cost forecasting & budgeting
- Real-time alerting
- Model recommendation engine
- LangChain integration

📦 Install: pip install token-calculator==2.1.0
📖 Docs: See PRD.md, ARCHITECTURE.md
💡 Examples: examples/ai_pm_daily_workflow.py

Full release notes: RELEASE_NOTES_v2.1.0.md
```

**Twitter/Social Media** (if applicable):
```
🎉 Just released Token Calculator v2.1.0!

Now with production-ready features for AI Product Managers:
✅ Multi-agent workflow tracking
✅ Cost forecasting & budgeting
✅ Context health monitoring
✅ Real-time alerting
✅ Model recommendations

pip install token-calculator==2.1.0

#AI #LLM #ProductManagement
```

---

## Post-Release Verification

### Check PyPI
- [ ] Package visible at https://pypi.org/project/token-calculator/
- [ ] Version 2.1.0 shows as latest
- [ ] README renders correctly
- [ ] Download stats updating

### Test Fresh Install
```bash
# In a fresh virtual environment
python -m venv test_env
source test_env/bin/activate
pip install token-calculator==2.1.0

# Run examples
python -c "
from token_calculator import CostTracker, create_storage

tracker = CostTracker(storage=create_storage('memory'))
tracker.track_call(model='gpt-4', input_tokens=100, output_tokens=50, agent_id='test')
report = tracker.get_costs(start_date='today')
print(f'✅ Basic functionality works! Cost: ${report.total_cost:.4f}')
"
```

### Monitor for Issues
- [ ] Check GitHub Issues for installation problems
- [ ] Monitor PyPI download stats
- [ ] Check for error reports

---

## Rollback Plan (If Needed)

If critical issues are found:

```bash
# 1. Yank the broken version from PyPI
twine upload --repository pypi --skip-existing dist/*

# 2. Fix issues in new branch
git checkout -b hotfix/v0.2.1
# Make fixes
git commit -m "fix: critical issue"
git push

# 3. Release v0.2.1
# Follow same release process
```

---

## Notes

### PyPI Token Setup (First Time)

1. Go to https://pypi.org/manage/account/token/
2. Create API token
3. Scope: Entire account or Project: token-calculator
4. Save token securely

Use token for upload:
```
Username: __token__
Password: pypi-AgE... (your token)
```

### Common Issues

**Issue**: `twine upload` fails with 403
**Fix**: Check PyPI token, ensure you have permissions

**Issue**: Package name conflict
**Fix**: Already own `token-calculator`, should be fine

**Issue**: README not rendering
**Fix**: Ensure README.md is valid markdown, no syntax errors

**Issue**: Missing dependencies
**Fix**: Check setup.py/pyproject.toml has all dependencies listed

---

## Success Criteria

Release is successful when:
- ✅ PyPI shows v2.1.0 as latest
- ✅ `pip install token-calculator==2.1.0` works
- ✅ All imports work in fresh environment
- ✅ Examples run without errors
- ✅ No critical issues reported in first 24 hours
- ✅ Download count starts increasing
- ✅ GitHub release created with notes
- ✅ Community notified

---

## Contact

If you encounter issues during release:
- Check https://status.python.org/ for PyPI status
- GitHub: https://github.com/arunaryamdn/token-calculator/issues
- Email: support@tokencalculator.com (if configured)

---

**Ready to release! 🚀**

Last Updated: 2026-01-24
Version: 2.1.0
