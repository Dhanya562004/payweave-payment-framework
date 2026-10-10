# Hyperswitch Open-Source Contribution Guide (`juspay/hyperswitch`)

This document contains the exact pull request title, description, and checklist to pass all automated GitHub Actions checks (including `amannn/action-semantic-pull-request` and `Verify PR contains one or more linked issues`) on [`juspay/hyperswitch`](https://github.com/juspay/hyperswitch).

---

## 🎯 Contribution Details
- **Target Repository**: `juspay/hyperswitch`
- **Issue**: [#14577](https://github.com/juspay/hyperswitch/issues/14577) — *[DOCS] Local setup guide doesn't mention protoc, which is required to build*
- **File Modified**: `docs/try_local_system.md`

---

## 🏷️ PR Title (Copy & Paste Exactly)
```text
docs(setup): add protoc installation instructions to local setup guide
```

> **Why this passes the PR Title Check**:
> - Uses lowercase type `docs` matching Conventional Commits.
> - Uses valid scope `(setup)`.
> - Description starts with a lowercase letter (`add`) and ends without a period or trailing punctuation.

---

## 📝 PR Description (Copy & Paste into GitHub PR Body)

```markdown
### 📌 Summary
This pull request updates the local system setup documentation (`docs/try_local_system.md`) to include installation instructions and verification commands for the Protocol Buffers compiler (`protoc`).

### 🔗 Linked Issue
Fixes #14577

### 🔍 Context & Problem
Building Hyperswitch locally requires `protoc` (Protocol Buffers compiler), but the setup guide previously omitted it from the dependency installation steps across several operating systems. This caused new contributors to encounter build errors during compilation.

### 🛠️ Changes Made
Added `protoc` installation and verification steps to all relevant operating-system setup sections:
1. **Ubuntu-based systems**: Added `sudo apt install protobuf-compiler` and `protoc --version`.
2. **Windows (Ubuntu on WSL2)**: Added `sudo apt install protobuf-compiler` and `protoc --version`.
3. **Windows (Native)**: Added `winget install --id Google.Protobuf` and `protoc --version`.
4. **macOS**: Added `brew install protobuf` and `protoc --version`.

All original instructions, formatting, and anchors in `docs/try_local_system.md` have been preserved.

### 🧪 Verification
- Verified `Google.Protobuf` package exists on Windows Package Manager (`winget show --id Google.Protobuf`) and delivers official `protoc` binaries.
- Confirmed `protoc --version` output across environments.
- Validated markdown formatting and relative link anchors.

### Checklist:
- [x] Description is comprehensive and self-explanatory.
- [x] Documentation follows Hyperswitch style guide.
- [x] Linked issue is referenced using `Fixes #14577`.
- [x] No breaking schema or code changes introduced.
```

---

## ⚙️ How to Fix the Two Failing Checks in GitHub Web UI

### 1. Fixing the PR Title Check (`Verify PR title follows conventional commit standards`)
1. Open your PR on GitHub: `https://github.com/juspay/hyperswitch/pull/<YOUR_PR_NUMBER>`.
2. Click the **Edit** button next to your PR title.
3. Replace the title with:
   ```text
   docs(setup): add protoc installation instructions to local setup guide
   ```
4. Click **Save**. The title check action will automatically re-run and pass ✅.

### 2. Fixing the Linked Issue Check (`Verify PR contains one or more linked issues`)
1. Click the **Edit** button on the first comment (your PR description).
2. Ensure the text `Fixes #14577` is present on its own line under `### 🔗 Linked Issue`.
3. Additionally, on the right sidebar of the PR page:
   - Look for the **Development** (or **Linked issues**) section.
   - Click the gear icon / link button.
   - Search for `14577` in `juspay/hyperswitch` and select it.
4. Once saved, GitHub will link the issue and the check will automatically turn green ✅.
