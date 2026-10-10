import React, { useState, useId } from 'react';

export interface UIConfig {
  brandName: string;
  primaryColor: string;
  layout: 'compact' | 'standard' | 'expanded';
  theme: 'minimal' | 'dark_glass' | 'light_corporate' | 'vibrant_fintech';
  methods: ('upi' | 'card' | 'netbanking')[];
  showSavedPayment: boolean;
  authMode?: 'frictionless' | 'adaptive' | 'always_2fa';
  apiEndpoint?: string;
}

export interface PaymentDetails {
  transactionId: string;
  amount: number;
  currency: string;
  method: string;
  provider: string;
  status: 'SUCCEEDED' | 'FAILED' | 'UNCERTAIN_TIMEOUT';
  retriesCount: number;
  idempotencyKey: string;
}

export interface PaymentErrorDetails {
  code: string;
  message: string;
  retryable: boolean;
  provider?: string;
}

export interface PayWeaveCheckoutProps {
  amount: number;
  currency?: string;
  merchantId?: string;
  config?: Partial<UIConfig>;
  onSuccess?: (details: PaymentDetails) => void;
  onFailure?: (error: PaymentErrorDetails) => void;
  simulateFailure?: boolean;
  simulateTimeout?: boolean;
}

export type CheckoutStatus =
  | 'idle'
  | 'validating'
  | 'authenticating'
  | 'processing'
  | 'success'
  | 'failure'
  | 'retryable_error';

export const PayWeaveCheckout: React.FC<PayWeaveCheckoutProps> = ({
  amount,
  currency = 'INR',
  merchantId = 'merchant_demo',
  config,
  onSuccess,
  onFailure,
  simulateFailure = false,
  simulateTimeout = false,
}) => {
  const formId = useId();
  const brandName = config?.brandName || 'Demo Merchant Store';
  const primaryColor = config?.primaryColor || '#6366F1';
  const methods = config?.methods || ['upi', 'card', 'netbanking'];
  const showSaved = config?.showSavedPayment ?? true;
  const authMode = config?.authMode || 'adaptive';

  const [selectedMethod, setSelectedMethod] = useState<'upi' | 'card' | 'netbanking'>(
    methods[0] || 'upi'
  );
  const [upiId, setUpiId] = useState('alex@okhdfcbank');
  const [cardNumber, setCardNumber] = useState('4532 1123 8894 1234');
  const [cardExpiry, setCardExpiry] = useState('12/28');
  const [cardCvv, setCardCvv] = useState('888');
  const [selectedBank, setSelectedBank] = useState('HDFC');

  const [status, setStatus] = useState<CheckoutStatus>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [providerUsed, setProviderUsed] = useState<string>('');
  const [retryCount, setRetryCount] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [idempotencyKey, setIdempotencyKey] = useState<string>(
    () => `idem_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
  );

  // Accessible Form Validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (amount <= 0) {
      newErrors.amount = 'Payment amount must be greater than zero.';
    }

    if (selectedMethod === 'upi') {
      const upiRegex = /^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$/;
      if (!upiId.trim()) {
        newErrors.upiId = 'UPI ID cannot be blank.';
      } else if (!upiRegex.test(upiId.trim())) {
        newErrors.upiId = 'Enter a valid UPI handle (e.g. username@bank).';
      }
    } else if (selectedMethod === 'card') {
      const cleanCard = cardNumber.replace(/\s+/g, '');
      if (!/^\d{16}$/.test(cleanCard)) {
        newErrors.cardNumber = 'Card number must be exactly 16 digits.';
      }
      if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(cardExpiry)) {
        newErrors.cardExpiry = 'Expiry date must be in MM/YY format.';
      }
      if (!/^\d{3,4}$/.test(cardCvv)) {
        newErrors.cardCvv = 'CVV must be 3 or 4 digits.';
      }
    } else if (selectedMethod === 'netbanking') {
      if (!selectedBank) {
        newErrors.bank = 'Please select a supported banking institution.';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePay = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isSubmitting) return; // Prevent duplicate submission

    if (!validateForm()) {
      setStatus('idle');
      return;
    }

    setIsSubmitting(true);
    setStatus('authenticating');
    setLogs([
      `[Idempotency] Key: ${idempotencyKey}`,
      `[Auth] Mode: ${authMode.toUpperCase()} — Evaluating risk heuristics...`,
    ]);

    await new Promise((r) => setTimeout(r, 400));

    // Simulated Authentication step-up
    if (authMode === 'always_2fa' || (authMode === 'adaptive' && amount > 20000)) {
      setLogs((prev) => [
        ...prev,
        '[Auth Step-Up] High value transaction triggered step-up OTP challenge (Simulated Passed).',
      ]);
    } else {
      setLogs((prev) => [...prev, '[Auth] Frictionless payment pathway approved.']);
    }

    setStatus('processing');
    setLogs((prev) => [
      ...prev,
      '[Routing] Consulting PayWeave Intelligent Scoring Router...',
    ]);

    await new Promise((r) => setTimeout(r, 500));

    // Simulated Timeout outcome
    if (simulateTimeout) {
      setStatus('retryable_error');
      setErrorMessage('Upstream bank connection timed out (Outcome Uncertain).');
      setLogs((prev) => [
        ...prev,
        '[Timeout] Upstream socket timeout 504. Outcome is UNCERTAIN.',
      ]);
      setIsSubmitting(false);
      if (onFailure) {
        onFailure({
          code: 'UNCERTAIN_TIMEOUT',
          message: 'Upstream gateway timed out. Please verify with merchant.',
          retryable: true,
        });
      }
      return;
    }

    // Simulated Failure outcome
    if (simulateFailure) {
      setStatus('failure');
      setErrorMessage('Bank rejected transaction: Insufficient funds (CARD_DECLINED).');
      setLogs((prev) => [
        ...prev,
        '[Terminal Error] Permanent business decline. Non-retryable.',
      ]);
      setIsSubmitting(false);
      if (onFailure) {
        onFailure({
          code: 'CARD_DECLINED',
          message: 'Bank rejected transaction: Insufficient funds.',
          retryable: false,
          provider: 'PSP-A',
        });
      }
      return;
    }

    // Simulated Success outcome via optimal PSP
    const candidatePsps = ['PSP-B', 'PSP-A', 'PSP-C'];
    const chosenPsp = candidatePsps[0];
    const txId = `tx_sim_${Date.now().toString(36)}`;

    setProviderUsed(chosenPsp);
    setStatus('success');
    setLogs((prev) => [
      ...prev,
      `[Router Decision] Best score: ${chosenPsp} (SLA Latency: 95ms).`,
      `[Confirmation] Captured ₹${amount.toLocaleString('en-IN')} (TxID: ${txId}).`,
    ]);
    setIsSubmitting(false);

    if (onSuccess) {
      onSuccess({
        transactionId: txId,
        amount,
        currency,
        method: selectedMethod,
        provider: chosenPsp,
        status: 'SUCCEEDED',
        retriesCount: retryCount,
        idempotencyKey,
      });
    }
  };

  const handleRetry = () => {
    setRetryCount((prev) => prev + 1);
    setStatus('idle');
    setErrorMessage('');
    // Generate new idempotency key on new attempt if needed
    setIdempotencyKey(`idem_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`);
  };

  const containerStyle: React.CSSProperties = {
    fontFamily: 'Inter, system-ui, sans-serif',
    maxWidth: '460px',
    margin: '0 auto',
    padding: '24px',
    borderRadius: '16px',
    background: '#1e293b',
    border: '1px solid #334155',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
    color: '#f8fafc',
  };

  const buttonStyle: React.CSSProperties = {
    width: '100%',
    padding: '14px',
    borderRadius: '10px',
    border: 'none',
    background: isSubmitting ? '#475569' : primaryColor,
    color: '#ffffff',
    fontWeight: 600,
    fontSize: '16px',
    cursor: isSubmitting ? 'not-allowed' : 'pointer',
    marginTop: '16px',
    transition: 'all 0.2s',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '8px',
  };

  return (
    <div style={containerStyle} role="region" aria-label="PayWeave Checkout Form">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700 }}>{brandName}</h2>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>
            Merchant: {merchantId} • PayWeave Framework
          </span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#38bdf8' }}>
            ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>{currency} (Simulated)</span>
        </div>
      </div>

      {/* IDLE / FORM INPUT STATE */}
      {status === 'idle' && (
        <form onSubmit={handlePay} noValidate>
          {showSaved && (
            <div
              style={{
                background: '#0f172a',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '16px',
                border: '1px solid #334155',
              }}
            >
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                ⚡ One-Click Saved Profile (Simulated)
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', fontWeight: 500 }}>
                <span>UPI: alex@okhdfcbank</span>
                <span style={{ color: '#10b981', fontSize: '12px' }}>Verified</span>
              </div>
            </div>
          )}

          {/* Payment Method Selector */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }} role="tablist" aria-label="Payment Methods">
            {methods.includes('upi') && (
              <button
                type="button"
                role="tab"
                aria-selected={selectedMethod === 'upi'}
                onClick={() => setSelectedMethod('upi')}
                style={{
                  flex: 1,
                  padding: '10px 6px',
                  borderRadius: '8px',
                  border: selectedMethod === 'upi' ? `2px solid ${primaryColor}` : '1px solid #475569',
                  background: selectedMethod === 'upi' ? '#334155' : '#0f172a',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                UPI Transfer
              </button>
            )}

            {methods.includes('card') && (
              <button
                type="button"
                role="tab"
                aria-selected={selectedMethod === 'card'}
                onClick={() => setSelectedMethod('card')}
                style={{
                  flex: 1,
                  padding: '10px 6px',
                  borderRadius: '8px',
                  border: selectedMethod === 'card' ? `2px solid ${primaryColor}` : '1px solid #475569',
                  background: selectedMethod === 'card' ? '#334155' : '#0f172a',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                Debit / Credit Card
              </button>
            )}

            {methods.includes('netbanking') && (
              <button
                type="button"
                role="tab"
                aria-selected={selectedMethod === 'netbanking'}
                onClick={() => setSelectedMethod('netbanking')}
                style={{
                  flex: 1,
                  padding: '10px 6px',
                  borderRadius: '8px',
                  border: selectedMethod === 'netbanking' ? `2px solid ${primaryColor}` : '1px solid #475569',
                  background: selectedMethod === 'netbanking' ? '#334155' : '#0f172a',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                NetBanking
              </button>
            )}
          </div>

          {/* Form Fields: UPI */}
          {selectedMethod === 'upi' && (
            <div>
              <label
                htmlFor={`${formId}-upi`}
                style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}
              >
                Enter Virtual Payment Address (VPA / UPI ID)
              </label>
              <input
                id={`${formId}-upi`}
                type="text"
                value={upiId}
                aria-invalid={Boolean(errors.upiId)}
                aria-describedby={errors.upiId ? `${formId}-upi-error` : undefined}
                onChange={(e) => {
                  setUpiId(e.target.value);
                  if (errors.upiId) setErrors((prev) => ({ ...prev, upiId: '' }));
                }}
                placeholder="username@bank"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '8px',
                  border: errors.upiId ? '1px solid #ef4444' : '1px solid #475569',
                  background: '#0f172a',
                  color: '#fff',
                  boxSizing: 'border-box',
                }}
              />
              {errors.upiId && (
                <div id={`${formId}-upi-error`} role="alert" style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px' }}>
                  {errors.upiId}
                </div>
              )}
            </div>
          )}

          {/* Form Fields: Card */}
          {selectedMethod === 'card' && (
            <div>
              <div style={{ marginBottom: '10px' }}>
                <label
                  htmlFor={`${formId}-card-num`}
                  style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}
                >
                  Card Number (Simulated)
                </label>
                <input
                  id={`${formId}-card-num`}
                  type="text"
                  value={cardNumber}
                  aria-invalid={Boolean(errors.cardNumber)}
                  onChange={(e) => {
                    setCardNumber(e.target.value);
                    if (errors.cardNumber) setErrors((prev) => ({ ...prev, cardNumber: '' }));
                  }}
                  maxLength={19}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '8px',
                    border: errors.cardNumber ? '1px solid #ef4444' : '1px solid #475569',
                    background: '#0f172a',
                    color: '#fff',
                    boxSizing: 'border-box',
                  }}
                />
                {errors.cardNumber && (
                  <div role="alert" style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px' }}>
                    {errors.cardNumber}
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1 }}>
                  <label
                    htmlFor={`${formId}-card-exp`}
                    style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}
                  >
                    Expiry (MM/YY)
                  </label>
                  <input
                    id={`${formId}-card-exp`}
                    type="text"
                    value={cardExpiry}
                    aria-invalid={Boolean(errors.cardExpiry)}
                    onChange={(e) => setCardExpiry(e.target.value)}
                    maxLength={5}
                    placeholder="12/28"
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: errors.cardExpiry ? '1px solid #ef4444' : '1px solid #475569',
                      background: '#0f172a',
                      color: '#fff',
                      boxSizing: 'border-box',
                    }}
                  />
                  {errors.cardExpiry && (
                    <div role="alert" style={{ color: '#ef4444', fontSize: '11px', marginTop: '4px' }}>
                      {errors.cardExpiry}
                    </div>
                  )}
                </div>

                <div style={{ flex: 1 }}>
                  <label
                    htmlFor={`${formId}-card-cvv`}
                    style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}
                  >
                    CVV
                  </label>
                  <input
                    id={`${formId}-card-cvv`}
                    type="password"
                    value={cardCvv}
                    aria-invalid={Boolean(errors.cardCvv)}
                    onChange={(e) => setCardCvv(e.target.value)}
                    maxLength={4}
                    placeholder="•••"
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: errors.cardCvv ? '1px solid #ef4444' : '1px solid #475569',
                      background: '#0f172a',
                      color: '#fff',
                      boxSizing: 'border-box',
                    }}
                  />
                  {errors.cardCvv && (
                    <div role="alert" style={{ color: '#ef4444', fontSize: '11px', marginTop: '4px' }}>
                      {errors.cardCvv}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Form Fields: NetBanking */}
          {selectedMethod === 'netbanking' && (
            <div>
              <label
                htmlFor={`${formId}-bank`}
                style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}
              >
                Select Banking Partner
              </label>
              <select
                id={`${formId}-bank`}
                value={selectedBank}
                onChange={(e) => setSelectedBank(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: '#0f172a',
                  color: '#fff',
                  boxSizing: 'border-box',
                }}
              >
                <option value="HDFC">HDFC Bank Direct</option>
                <option value="SBI">State Bank of India</option>
                <option value="ICICI">ICICI Bank Internet Banking</option>
                <option value="AXIS">Axis Bank Corporate</option>
              </select>
            </div>
          )}

          {errors.amount && (
            <div role="alert" style={{ color: '#ef4444', fontSize: '12px', marginTop: '8px' }}>
              {errors.amount}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            style={buttonStyle}
            id="payweave-submit-btn"
          >
            Pay ₹{amount.toLocaleString('en-IN')}
          </button>
        </form>
      )}

      {/* AUTHENTICATING / PROCESSING STATE */}
      {(status === 'authenticating' || status === 'processing') && (
        <div style={{ textAlign: 'center', padding: '30px 0' }} role="status" aria-live="polite">
          <div style={{ fontSize: '32px', marginBottom: '12px' }} className="animate-spin">⚙️</div>
          <div style={{ fontWeight: 600, fontSize: '16px', marginBottom: '8px' }}>
            {status === 'authenticating' ? 'Evaluating Adaptive Risk & Security...' : 'Executing Intelligent Provider Route...'}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            Idempotency Key locked. Dispatching to highest-health PSP candidate...
          </div>
        </div>
      )}

      {/* SUCCESS STATE */}
      {status === 'success' && (
        <div style={{ textAlign: 'center', padding: '24px 0' }} role="status">
          <div style={{ fontSize: '44px', color: '#10b981', marginBottom: '8px' }}>✓</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#10b981' }}>Payment Confirmed!</div>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>
            Routed via <strong>{providerUsed}</strong>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            Idempotency Key: {idempotencyKey}
          </div>
          <button
            onClick={() => {
              setStatus('idle');
              setIdempotencyKey(`idem_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`);
            }}
            style={{ ...buttonStyle, marginTop: '20px', background: '#334155' }}
          >
            Start New Transaction
          </button>
        </div>
      )}

      {/* TERMINAL FAILURE STATE */}
      {status === 'failure' && (
        <div style={{ textAlign: 'center', padding: '24px 0' }} role="alert">
          <div style={{ fontSize: '44px', color: '#ef4444', marginBottom: '8px' }}>✕</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#ef4444' }}>Payment Failed</div>
          <div style={{ fontSize: '13px', color: '#cbd5e1', marginTop: '6px' }}>{errorMessage}</div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            Non-retryable domain error. Please use another payment instrument.
          </div>
          <button
            onClick={() => setStatus('idle')}
            style={{ ...buttonStyle, marginTop: '20px', background: '#334155' }}
          >
            Try Different Method
          </button>
        </div>
      )}

      {/* RETRYABLE ERROR STATE */}
      {status === 'retryable_error' && (
        <div style={{ textAlign: 'center', padding: '24px 0' }} role="alert">
          <div style={{ fontSize: '44px', color: '#f59e0b', marginBottom: '8px' }}>⚠️</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#f59e0b' }}>Network Timeout / Transient Error</div>
          <div style={{ fontSize: '13px', color: '#cbd5e1', marginTop: '6px' }}>{errorMessage}</div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            Outcome is uncertain. Safe to retry with failover provider.
          </div>
          <button
            onClick={handleRetry}
            style={{ ...buttonStyle, marginTop: '20px', background: '#d97706' }}
          >
            Retry Payment (Attempt #{retryCount + 1})
          </button>
        </div>
      )}

      {/* Runtime Execution Logs */}
      {logs.length > 0 && (
        <div style={{ marginTop: '20px', background: '#0f172a', padding: '10px', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace', color: '#38bdf8' }}>
          <div style={{ color: '#94a3b8', marginBottom: '4px' }}>Operational Audit Log:</div>
          {logs.map((log, idx) => (
            <div key={idx}>&gt; {log}</div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '16px', fontSize: '10px', textAlign: 'center', color: '#64748b' }}>
        🔒 Simulated Portfolio Framework — Never moves real fiat currency or exposes secrets.
      </div>
    </div>
  );
};
