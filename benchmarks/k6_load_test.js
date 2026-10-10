import http from 'k6/http';
import { check, sleep } from 'k6';

// k6 Load Test Configuration for PayWeave Payment Gateway API
export const options = {
  stages: [
    { duration: '10s', target: 20 },  // Ramp up to 20 virtual users
    { duration: '30s', target: 50 },  // Maintain peak load of 50 VUs
    { duration: '10s', target: 0 },   // Graceful ramp down
  ],
  thresholds: {
    // 95% of requests must complete under 200ms; 99% under 500ms
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    // Error rate must stay below 2%
    http_req_failed: ['rate<0.02'],
  },
};

const BASE_URL = __ENV.PAYWEAVE_API_URL || 'http://localhost:8000';

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // 1. Benchmark: POST /routing/decision (Intelligent Multi-Factor Scoring)
  const routingPayload = JSON.stringify({
    amount: 1499.0 + Math.random() * 1000,
    currency: 'INR',
    payment_method: 'upi',
    customer_id: `cust_k6_${__VU}`,
    risk_score: 0.12,
  });

  const routingRes = http.post(`${BASE_URL}/routing/decision`, routingPayload, { headers });
  check(routingRes, {
    'routing status is 200': (r) => r.status === 200,
    'routing returned selected provider': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.selected_provider !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  // 2. Benchmark: POST /payment/create (ACID State Machine & Idempotency)
  const uniqueKey = `idemp_k6_${__VU}_${__ITER}_${Date.now()}`;
  const createPayload = JSON.stringify({
    amount: 2500.0,
    currency: 'INR',
    payment_method: 'card',
    customer_id: `cust_k6_${__VU}`,
    idempotency_key: uniqueKey,
  });

  const createRes = http.post(`${BASE_URL}/payment/create`, createPayload, { headers });
  check(createRes, {
    'payment create status is 200/201': (r) => r.status === 200 || r.status === 201,
    'payment status is CREATED': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'CREATED';
      } catch (e) {
        return false;
      }
    },
  });

  // 3. Benchmark: POST /payment/simulate (End-to-End Gateway Processing)
  const simPayload = JSON.stringify({
    amount: 999.0,
    currency: 'INR',
    payment_method: 'upi',
    customer_id: `cust_k6_${__VU}`,
    risk_score: 0.05,
  });

  const simRes = http.post(`${BASE_URL}/payment/simulate`, simPayload, { headers });
  check(simRes, {
    'simulation status is 200': (r) => r.status === 200,
    'simulation has transaction_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.transaction_id !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  sleep(0.1); // Small pacing delay between iterations
}
