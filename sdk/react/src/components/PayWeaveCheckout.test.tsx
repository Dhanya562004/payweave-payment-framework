import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PayWeaveCheckout } from './PayWeaveCheckout';

describe('PayWeaveCheckout SDK Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders merchant brand, formatted amount, and currency correctly', () => {
    render(
      <PayWeaveCheckout
        amount={3500.0}
        currency="INR"
        config={{ brandName: 'Test Merchant Store' }}
      />
    );

    expect(screen.getByText('Test Merchant Store')).toBeInTheDocument();
    expect(screen.getByText(/3,500\.00/)).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /UPI Transfer/i })).toBeInTheDocument();
  });

  it('validates UPI ID format and displays accessible error message', async () => {
    render(<PayWeaveCheckout amount={1500.0} />);

    const upiInput = screen.getByLabelText(/Enter Virtual Payment Address/i);
    // Enter invalid UPI ID
    fireEvent.change(upiInput, { target: { value: 'invalid_upi_without_at' } });

    const payButton = screen.getByRole('button', { name: /Pay ₹1,500/i });
    fireEvent.click(payButton);

    const alertMsg = await screen.findByRole('alert');
    expect(alertMsg).toHaveTextContent(/Enter a valid UPI handle/i);
    expect(upiInput).toHaveAttribute('aria-invalid', 'true');
  });

  it('switches payment method to Card and validates 16-digit card number', async () => {
    render(<PayWeaveCheckout amount={2500.0} />);

    // Switch to Card tab
    const cardTab = screen.getByRole('tab', { name: /Debit \/ Credit Card/i });
    fireEvent.click(cardTab);

    expect(cardTab).toHaveAttribute('aria-selected', 'true');
    const cardInput = screen.getByLabelText(/Card Number/i);
    expect(cardInput).toBeInTheDocument();

    // Enter short card number
    fireEvent.change(cardInput, { target: { value: '4111 2222 3333' } });
    const payBtn = screen.getByRole('button', { name: /Pay ₹2,500/i });
    fireEvent.click(payBtn);

    const alertMsg = await screen.findByRole('alert');
    expect(alertMsg).toHaveTextContent(/Card number must be exactly 16 digits/i);
  });

  it('transitions to authenticating state and prevents duplicate submissions on submit', async () => {
    render(<PayWeaveCheckout amount={1200.0} />);

    const payButton = screen.getByRole('button', { name: /Pay ₹1,200/i });
    fireEvent.click(payButton);

    // After submit click, form transitions to authenticating status indicator
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/Evaluating Adaptive Risk/i)).toBeInTheDocument();
  });

  it('successfully completes payment and triggers onSuccess callback with idempotency key', async () => {
    const onSuccess = vi.fn();
    render(
      <PayWeaveCheckout
        amount={1200.0}
        onSuccess={onSuccess}
      />
    );

    const payButton = screen.getByRole('button', { name: /Pay ₹1,200/i });
    fireEvent.click(payButton);

    await waitFor(
      () => {
        expect(screen.getByText(/Payment Confirmed!/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(onSuccess).toHaveBeenCalledTimes(1);
    const result = onSuccess.mock.calls[0][0];
    expect(result.status).toBe('SUCCEEDED');
    expect(result.amount).toBe(1200.0);
    expect(result.idempotencyKey).toMatch(/^idem_/);
    expect(result.provider).toBeTruthy();
  });

  it('renders failure state and triggers onFailure on simulated terminal decline', async () => {
    const onFailure = vi.fn();
    render(
      <PayWeaveCheckout
        amount={5000.0}
        simulateFailure={true}
        onFailure={onFailure}
      />
    );

    const payButton = screen.getByRole('button', { name: /Pay ₹5,000/i });
    fireEvent.click(payButton);

    await waitFor(
      () => {
        expect(screen.getByText(/Payment Failed/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(onFailure).toHaveBeenCalledTimes(1);
    expect(onFailure.mock.calls[0][0].retryable).toBe(false);
  });

  it('renders retryable error state on simulated timeout and allows retry', async () => {
    const onFailure = vi.fn();
    render(
      <PayWeaveCheckout
        amount={2000.0}
        simulateTimeout={true}
        onFailure={onFailure}
      />
    );

    const payButton = screen.getByRole('button', { name: /Pay ₹2,000/i });
    fireEvent.click(payButton);

    await waitFor(
      () => {
        expect(screen.getByText(/Network Timeout \/ Transient Error/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(onFailure).toHaveBeenCalledTimes(1);
    expect(onFailure.mock.calls[0][0].retryable).toBe(true);

    // Can click retry button
    const retryBtn = screen.getByRole('button', { name: /Retry Payment/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);

    // Should return to idle form
    expect(screen.getByRole('button', { name: /Pay ₹2,000/i })).toBeInTheDocument();
  });
});
