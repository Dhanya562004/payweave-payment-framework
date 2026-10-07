import React, { useState } from 'react';

export interface UIConfig {
  brandName: string;
  primaryColor: string;
  layout: 'compact' | 'standard' | 'expanded';
  theme: 'minimal' | 'dark_glass' | 'light_corporate' | 'vibrant_fintech';
  methods: string[];
  showSavedPayment: boolean;
}

export interface PayWeaveCheckoutProps {
  amount: number;
  currency: string;
  config?: Partial<UIConfig>;
  onSuccess?: (details: any) => void;
  onFailure?: (error: any) => void;
}

export const PayWeaveCheckout: React.FC<PayWeaveCheckoutProps> = ({
  amount,
  currency = 'INR',
  config,
  onSuccess,
  onFailure,
}) => {
  const brandName = config?.brandName || 'Demo Merchant Store';
  const primaryColor = config?.primaryColor || '#6366F1';
  const methods = config?.methods || ['upi', 'card'];
  const showSaved = config?.showSavedPayment ?? true;

  const [selectedMethod, setSelectedMethod] = useState<string>(methods[0] || 'upi');
  const [upiId, setUpiId] = useState('demo@upi');
  const [cardNumber, setCardNumber] = useState('4000 0000 0000 1234');
  const [status, setStatus] = useState<'idle' | 'authenticating' | 'processing' | 'success' | 'failed'>('idle');
  const [providerUsed, setProviderUsed] = useState<string>('');
  const [retryCount, setRetryCount] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);

  const handlePay = async () => {
    setStatus('authenticating');
    setLogs(['Evaluating risk score & adaptive authentication...']);

    await new Promise((r) => setTimeout(r, 800));

    if (amount > 10000) {
      setLogs((prev) => [...prev, 'Step-up 2FA triggered for high value transaction.']);
    }

    setStatus('processing');
    setLogs((prev) => [...prev, 'Querying PayWeave Intelligent Router for optimal PSP...']);

    await new Promise((r) => setTimeout(r, 1200));

    // Simulated provider selection outcome
    const pspList = ['psp-b', 'psp-a', 'psp-c'];
    const chosenPsp = pspList[Math.floor(Math.random() * pspList.length)];
    const isFallback = Math.random() > 0.7;

    if (isFallback) {
      setRetryCount(1);
      setLogs((prev) => [...prev, 'PSP-A latency spike detected. Auto-rerouting via PSP-B fallback...']);
    }

    setProviderUsed(chosenPsp.toUpperCase());
    setStatus('success');
    setLogs((prev) => [...prev, `Payment confirmed via ${chosenPsp.toUpperCase()}!`]);

    if (onSuccess) {
      onSuccess({ amount, currency, provider: chosenPsp, status: 'SUCCESS' });
    }
  };

  const containerStyle: React.CSSProperties = {
    fontFamily: 'Inter, system-ui, sans-serif',
    maxWidth: '440px',
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
    background: primaryColor,
    color: '#ffffff',
    fontWeight: 600,
    fontSize: '16px',
    cursor: 'pointer',
    marginTop: '16px',
    transition: 'all 0.2s',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700 }}>{brandName}</h3>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Powered by PayWeave Framework</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#38bdf8' }}>
            ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>{currency}</span>
        </div>
      </div>

      {status === 'idle' && (
        <>
          {showSaved && (
            <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', marginBottom: '16px', border: '1px stroke #334155' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>⚡ One-Click Saved Payment</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', fontWeight: 500 }}>
                <span>UPI: alex@okaxis</span>
                <span style={{ color: '#10b981', fontSize: '12px' }}>Verified</span>
              </div>
            </div>
          )}

          {/* Payment Method Selector */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {methods.includes('upi') && (
              <button
                onClick={() => setSelectedMethod('upi')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  border: selectedMethod === 'upi' ? `2px solid ${primaryColor}` : '1px solid #475569',
                  background: selectedMethod === 'upi' ? '#334155' : '#0f172a',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                UPI Transfer
              </button>
            )}

            {methods.includes('card') && (
              <button
                onClick={() => setSelectedMethod('card')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  border: selectedMethod === 'card' ? `2px solid ${primaryColor}` : '1px solid #475569',
                  background: selectedMethod === 'card' ? '#334155' : '#0f172a',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                Card / NetBanking
              </button>
            )}
          </div>

          {/* Form Fields */}
          {selectedMethod === 'upi' ? (
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Enter VPA / UPI ID</label>
              <input
                type="text"
                value={upiId}
                onChange={(e) => setUpiId(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #475569', background: '#0f172a', color: '#fff', boxSizing: 'border-box' }}
              />
            </div>
          ) : (
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Card Number (Simulation Data Only)</label>
              <input
                type="text"
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #475569', background: '#0f172a', color: '#fff', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <button onClick={handlePay} style={buttonStyle}>
            Pay ₹{amount.toLocaleString('en-IN')}
          </button>
        </>
      )}

      {(status === 'authenticating' || status === 'processing') && (
        <div style={{ textAlign: 'center', padding: '30px 0' }}>
          <div style={{ fontSize: '28px', marginBottom: '12px' }}>⚙️</div>
          <div style={{ fontWeight: 600, fontSize: '16px', marginBottom: '8px' }}>
            {status === 'authenticating' ? 'Adaptive Security Check...' : 'Executing Intelligent Payment Route...'}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Evaluating risk, routing score, and latency SLAs...</div>
        </div>
      )}

      {status === 'success' && (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <div style={{ fontSize: '40px', color: '#10b981', marginBottom: '8px' }}>✓</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#10b981' }}>Payment Successful!</div>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>Processed via {providerUsed}</div>
          {retryCount > 0 && (
            <div style={{ fontSize: '11px', color: '#f59e0b', marginTop: '4px' }}>⚡ Auto-Recovered via Intelligent Fallback</div>
          )}
          <button onClick={() => setStatus('idle')} style={{ ...buttonStyle, marginTop: '20px', background: '#334155' }}>
            New Transaction
          </button>
        </div>
      )}

      {/* Execution Timeline Logs */}
      {logs.length > 0 && (
        <div style={{ marginTop: '20px', background: '#0f172a', padding: '10px', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace', color: '#38bdf8' }}>
          <div style={{ color: '#94a3b8', marginBottom: '4px' }}>Runtime Execution Log:</div>
          {logs.map((log, idx) => (
            <div key={idx}>&gt; {log}</div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '16px', fontSize: '10px', textAlign: 'center', color: '#64748b' }}>
        🔒 Portfolio Simulation Framework — No real money or credentials handled.
      </div>
    </div>
  );
};
