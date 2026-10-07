import React from 'react';
import { PayWeaveCheckout } from './components/PayWeaveCheckout';

export const App: React.FC = () => {
  return (
    <div style={{ padding: '40px 20px', minHeight: '100vh', background: '#0f172a' }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', color: '#6366f1', margin: 0 }}>PayWeave React Merchant SDK</h1>
        <p style={{ color: '#94a3b8', fontSize: '14px' }}>Declarative Configurable Checkout Component Demo</p>
      </div>

      <PayWeaveCheckout
        amount={4999.0}
        currency="INR"
        config={{
          brandName: 'Apex Electronics Online',
          primaryColor: '#6366F1',
          layout: 'compact',
          methods: ['upi', 'card'],
          showSavedPayment: true,
        }}
        onSuccess={(details) => console.log('Payment Completed:', details)}
      />
    </div>
  );
};
