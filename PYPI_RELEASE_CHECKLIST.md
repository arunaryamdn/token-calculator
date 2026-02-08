# PyPI Release Checklist for v2.2.0

## Pre-Release Verification

### 1. Version Check
- [x] Version bumped in `token_calculator/__init__.py` (2.1.0 → 2.2.0)
- [x] Version matches in `pyproject.toml`

### 2. Code Quality
- [x] All imports working correctly
- [x] No syntax errors
- [x] Security vulnerabilities fixed (SQL injection, SSRF, connection leaks)
- [x] Run tests: `pytest` (101 tests passing, 49% coverage)
- [x] Check for linting issues: `black`, `isort`, `flake8`, `mypy`
- [x] Security scan: `bandit` (no issues)

### 3. Documentation
- [x] README.md verified
- [x] CHANGELOG.md updated with v2.2.0
- [x] SECURITY.md created
- [x] Docstrings complete with security notes

### 4. Git
- [x] All changes committed (5 commits)
- [x] Changes pushed to GitHub
- [x] All CI checks passing
- [x] Repository cleaned up

---

## Release Steps

### Step 1: Merge PR to Main

```bash
# After PR approval, merge to main
git checkout main
git pull origin main
```

### Step 2: Create GitHub Release

1. Go to: https://github.com/arunaryamdn/token-calculator/releases/new
2. Click "Choose a tag" dropdown
3. Type: v2.2.0
4. Click "Create new tag: v2.2.0 on publish"
5. Release title: "v2.2.0 - Security Fixes and Comprehensive Testing"
6. Copy release notes from CHANGELOG.md (v2.2.0 section)
7. Mark as "Latest release"
8. Publish release

**Note**: The publish.yml workflow will automatically trigger and build/upload to PyPI

### Step 3: Wait for GitHub Actions

After publishing the release, the GitHub Actions workflow will automatically:
1. Build the package
2. Run all tests
3. Upload to PyPI

Monitor the workflow at:
https://github.com/arunaryamdn/token-calculator/actions

### Step 4: Verify PyPI Release

```bash
# Wait a few minutes, then install from PyPI
pip uninstall token-calculator -y
pip install token-calculator==2.2.0

# Verify version
python -c "import token_calculator; print(token_calculator.__version__)"
# Should print: 2.2.0

# Test security features
python -c "
from token_calculator import (
    CostTracker,
    ValidationError,
    SecurityError,
    validate_sql_identifier,
    validate_webhook_url,
    create_storage
)
print('✅ All security features available!')
print('✅ Version 2.2.0 successfully published!')
"
```

### Step 5: Update GitHub

1. README badge will auto-update to show v2.2.0
2. Close related security issues
3. Announce in Discussions

### Step 6: Announce Release

**GitHub Discussions**:
```
🔒 Token Calculator v2.2.0 Released - Security & Testing Update

We're excited to announce v2.2.0 - a security-focused release with comprehensive testing improvements!

🔒 Security Fixes:
- SQL injection prevention (filter keys, group_by validation)
- SSRF prevention (webhook URL validation)
- Connection leak fixes (proper resource cleanup)
- Input validation (DoS prevention)
- Thread safety (race condition fixes)

✅ Quality Improvements:
- 101+ tests with 49% code coverage (up from ~15%)
- Comprehensive security test suite
- GitHub Actions CI/CD pipeline
- Type hints and strict mypy checking
- Structured logging throughout

📦 Install: pip install token-calculator==2.2.0
📖 Security: See SECURITY.md
📝 Full changes: CHANGELOG.md

100% backward compatible - upgrade recommended for all users!
```

**Twitter/Social Media** (if applicable):
```
🔒 Token Calculator v2.2.0 released!

Major security & testing update:
✅ SQL injection prevention
✅ SSRF prevention
✅ 101+ tests (49% coverage)
✅ CI/CD pipeline
✅ 100% backward compatible

Upgrade now: pip install token-calculator==2.2.0

#Security #Testing #Python
```

---

## Post-Release Verification

### Check PyPI
- [ ] Package visible at https://pypi.org/project/token-calculator/
- [ ] Version 2.2.0 shows as latest
- [ ] README renders correctly
- [ ] Download stats updating

### Test Fresh Install
```bash
# In a fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate
pip install token-calculator==2.2.0

# Test basic functionality
python -c "
from token_calculator import CostTracker, create_storage

tracker = CostTracker(storage=create_storage('memory'))
tracker.track_call(model='gpt-4', input_tokens=100, output_tokens=50, agent_id='test')
report = tracker.get_costs(start_date='today')
print(f'✅ Basic functionality works! Cost: ${report.total_cost:.4f}')
"

# Test security features
python -c "
from token_calculator import validate_sql_identifier, ValidationError

try:
    validate_sql_identifier('valid_name')
    print('✅ Valid identifier accepted')
    validate_sql_identifier('DROP TABLE')
except ValidationError:
    print('✅ SQL injection prevented')
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
- ✅ GitHub Actions workflow completes successfully
- ✅ PyPI shows v2.2.0 as latest
- ✅ `pip install token-calculator==2.2.0` works
- ✅ All imports work in fresh environment
- ✅ Security features work as expected
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

Last Updated: 2026-02-08
Version: 2.2.0
