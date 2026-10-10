# Juspay Hyperswitch Open-Source Contribution Guide

This guide gives you a turnkey, ready-to-submit Pull Request to Juspay's flagship open-source project, **[Hyperswitch](https://github.com/juspay/hyperswitch)**. Submitting this PR directly matches the Juspay JD requirement for open-source initiative and functional Rust/Haskell systems.

---

## 🚀 How to Submit in 3 Easy Steps

### Step 1: Fork the Hyperswitch Repository
1. Navigate to [https://github.com/juspay/hyperswitch](https://github.com/juspay/hyperswitch).
2. Click the **Fork** button (top-right) into your personal GitHub account (`Dhanya562004`).
3. Clone your fork locally or use the GitHub Web Editor (`.` key on your fork page).

### Step 2: Apply the Contribution
Refer to [`PR_PROPOSAL.md`](PR_PROPOSAL.md) in this folder.
- **Contribution Area**: Connector error code categorization & Indian payment switch retry documentation for UPI Intent/Collect and Netbanking failovers.
- Copy the provided changes from `PR_PROPOSAL.md` into your fork's branch:
  ```bash
  git checkout -b fix/upi-connector-retry-classification
  # Apply the changes specified in PR_PROPOSAL.md
  git commit -m "docs(connectors): clarify UPI error categorization and non-retryable response codes"
  git push origin fix/upi-connector-retry-classification
  ```

### Step 3: Open the Pull Request on `juspay/hyperswitch`
1. Navigate to [https://github.com/juspay/hyperswitch/pulls](https://github.com/juspay/hyperswitch/pulls).
2. Click **New Pull Request**.
3. Choose `base: main` <- `compare: Dhanya562004:fix/upi-connector-retry-classification`.
4. Copy and paste the PR Title and Markdown description from `PR_PROPOSAL.md`.
5. Click **Create pull request**!
