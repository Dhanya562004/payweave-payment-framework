import React, { useState } from 'react';
import { PayWeaveCheckout, PaymentDetails, PaymentErrorDetails } from './components/PayWeaveCheckout';

export const App: React.FC = () => {
  const [simulationMode, setSimulationMode] = useState<'normal' | 'timeout' | 'failure'>('normal');
  const [amount, setAmount] = useState<number>(4999.0);
  const [lastCallback, setLastCallback] = useState<string | null>(null);

  return (
    <div style={{ padding: '40px 20px', minHeight: '100vh', background: '#0b1120', color: '#f8fafc', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ maxWidth: '780px', margin: '0 auto', textAlign: 'center', marginBottom: '28px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 800, color: '#818cf8', margin: '0 0 8px 0' }}>
          PayWeave React Merchant Checkout SDK
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
          Declarative Multi-Method Checkout Component with Idempotency & Fault-Tolerant Routing
        </p>
        <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 12px', borderRadius: '999px', background: '#1e293b', border: '1px solid #334155', fontSize: '11px', color: '#38bdf8' }}>
          🔒 SIMULATED PORTFOLIO DEMO — All Provider Transactions Simulated
        </div>
      </div>

      {/* Simulation Controls Dashboard */}
      <div style={{ maxWidth: '460px', margin: '0 auto 24px auto', background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', marginBottom: '10px' }}>
          Simulation Scenario Controls:
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setSimulationMode('normal')}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '6px',
              border: simulationMode === 'normal' ? '2px solid #10b981' : '1px solid #475569',
              background: simulationMode === 'normal' ? '#064e3b' : '#0f172a',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Normal Success
          </button>
          <button
            type="button"
            onClick={() => setSimulationMode('timeout')}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '6px',
              border: simulationMode === 'timeout' ? '2px solid #f59e0b' : '1px solid #475569',
              background: simulationMode === 'timeout' ? '#78350f' : '#0f172a',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Bank Timeout
          </button>
          <button
            type="button"
            onClick={() => setSimulationMode('failure')}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '6px',
              border: simulationMode === 'failure' ? '2px solid #ef4444' : '1px solid #475569',
              background: simulationMode === 'failure' ? '#7f1d1d' : '#0f172a',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Card Decline
          </button>
        </div>
      </div>

      {/* The Core SDK Component */}
      <PayWeaveCheckout
        amount={amount}
        currency="INR"
        merchantId="apex_store_demo"
        config={{
          brandName: 'Apex Electronics Online',
          primaryColor: '#6366F1',
          layout: 'compact',
          methods: ['upi', 'card', 'netbanking'],
          showSavedPayment: true,
          authMode: 'adaptive',
        }}
        simulateTimeout={simulationMode === 'timeout'}
        simulateFailure={simulationMode === 'failure'}
        onSuccess={(details: PaymentDetails) => {
          setLastCallback(`[onSuccess] Payment ${details.transactionId} confirmed via ${details.provider} (Idempotency Key: ${details.idempotencyKey})`);
        }}
        onFailure={(err: PaymentErrorDetails) => {
          setLastCallback(`[onFailure] Code: ${err.code} — ${err.message} (Retryable: ${err.retryable})`);
        }}
      />

      {/* Live Callback Event Stream */}
      {lastCallback && (
        <div style={{ maxWidth: '460px', margin: '20px auto 0 auto', padding: '12px', borderRadius: '8px', background: '#0f172a', border: '1px solid #38bdf8', fontSize: '11px', fontFamily: 'monospace', color: '#7dd3fc' }}>
          <strong>Merchant Callback Received:</strong>
          <div style={{ marginTop: '4px' }}>{lastCallback}</div>
        </div>
      )}
    </div>
  );
};
