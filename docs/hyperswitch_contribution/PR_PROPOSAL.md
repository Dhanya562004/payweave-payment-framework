# Ready-to-Submit Pull Request for `juspay/hyperswitch`

## Proposed PR Title:
```
docs(connectors): standardize UPI error classification matrix and circuit-breaker retry rules
```

---

## PR Description (Copy & Paste directly into GitHub PR description):

### 📌 Summary
This pull request standardizes the error code taxonomy and retry eligibility matrix for Indian payment rails (UPI Intent, UPI Collect, and Netbanking) across payment connector integrations.

### 🔍 Context & Problem
In high-throughput payment switches, downstream PSPs return varied error codes during bank downtimes and account-level declines:
- Transient network anomalies (e.g., `U19` - Bank server unreachable, `U30` - NPCI switch timeout) require circuit-breaker tracking and automatic failover retries.
- Terminal business errors (e.g., `ZM` - Invalid UPI PIN, `ZA` - Account blocked/frozen, `ZH` - Exceeds transaction limit) must be classified as **non-retryable** to prevent unnecessary load on banking switches and eliminate duplicate consumer debit attempts.

Previously, connector error handling documentation lacked an explicit classification table contrasting retryable technical timeouts against non-retryable account exceptions.

### 🛠️ Changes Proposed
1. **Error Categorization Matrix**: Added comprehensive classification tables documenting:
   - `RETRYABLE_TRANSIENT`: Network timeouts, gateway connection resets, internal switch 503s.
   - `NON_RETRYABLE_TERMINAL`: Authentication failures, insufficient funds, expired VPA/handle.
   - `UNCERTAIN_PENDING`: In-flight transactions requiring webhook deduplication or poll reconciliations.
2. **Connector Best Practices**: Documented circuit-breaker probe cooldown behavior (`CLOSED -> OPEN -> HALF_OPEN`) for UPI connectors.

### 🧪 Verification & Testing
- Validated markdown formatting and hyperlink anchors with markdown linter.
- Ensured consistency with Hyperswitch's unified error code schema (`types::api::enums`).

---

### Checklist:
- [x] Description is comprehensive and self-explanatory.
- [x] Documentation follows Hyperswitch style guide.
- [x] No breaking schema changes introduced.
