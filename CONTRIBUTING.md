# Contributing to Radnex

Thank you for your interest in contributing to **Radnex**! We welcome community contributions to help improve autonomous web-application reconnaissance and security engineering.

---

## 🛠️ Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/thecnical/Radnex.git
   cd Radnex
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Verify Environment:**
   Run the verification script:
   ```bash
   ./setup.sh
   ```

---

## 🧪 Running Tests

Radnex maintains high test coverage with regression suites in `tests/`.

Run individual suites:
```bash
python tests/test_antseed.py
python tests/test_routing.py
python tests/test_gateway_auth.py
```

Run the entire test suite across all 35 test files:
```bash
python -c "
import subprocess, sys, pathlib
tests = sorted(pathlib.Path('tests').glob('test_*.py'))
failures = []
for t in tests:
    res = subprocess.run([sys.executable, str(t)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f'FAIL: {t.name}')
        failures.append((t.name, res.stdout, res.stderr))
    else:
        print(f'PASS: {t.name}')
if failures:
    for name, out, err in failures:
        print('='*50)
        print(f'FAILURE in {name}:\n{out}\n{err}')
    sys.exit(1)
print(f'\nAll {len(tests)} test suites passed!')
"
```

All 35 test suites must pass before submitting a pull request.

---

## 📋 Pull Request Guidelines

1. **Branch Naming:**
   - `feat/feature-name`
   - `fix/bug-description`
   - `docs/update-guide`
2. **Commit Messages:**
   Follow Conventional Commits (e.g., `feat(antseed): ...`, `fix(routing): ...`, `docs: ...`).
3. **Safety & Code Hygiene:**
   - Never commit API keys, personal credentials, or live tokens.
   - Maintain defensive coding practices and handle network exceptions gracefully.
   - Preserve existing regression assertions.

---

## ⚖️ Code of Conduct

Please adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all project interactions.
