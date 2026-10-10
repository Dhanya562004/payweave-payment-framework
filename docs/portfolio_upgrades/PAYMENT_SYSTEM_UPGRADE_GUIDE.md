# Payment System Portfolio Upgrade Guide

Use this guide to upgrade your standalone **Payment System** repository to hit the Tier 3 Juspay engineering criteria:
1. `k6` load test measuring real throughput and p95 latency.
2. JaCoCo test coverage enforcement (> 80%).
3. Dead-Letter Queue (DLQ) replay endpoint.

---

## 1. Drop-In `k6` Load Test Script (`k6_payment_system.js`)

Save this file in `benchmarks/k6_payment_system.js` in your Payment System repository:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 30 },  // Ramp-up
    { duration: '30s', target: 60 },  // Steady peak
    { duration: '15s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<150', 'p(99)<300'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    amount: 1999.0,
    currency: 'INR',
    paymentMethod: 'UPI',
    idempotencyKey: `pay_${__VU}_${__ITER}_${Date.now()}`,
  });

  const res = http.post(`${BASE_URL}/api/v1/payments`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
  });

  sleep(0.05);
}
```

Run with:
```bash
k6 run benchmarks/k6_payment_system.js
```

---

## 2. JaCoCo Code Coverage (Maven `pom.xml`)

Add to `<plugins>` in your `pom.xml`:

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
        <execution>
            <id>check</id>
            <goals>
                <goal>check</goal>
            </goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

Run with:
```bash
mvn clean test jacoco:report
```

---

## 3. Dead-Letter Queue (DLQ) Replay Endpoint (Spring Boot)

Add this controller to allow on-call SREs to replay poisoned payment events:

```java
@RestController
@RequestMapping("/api/v1/dlq")
public class DlqReplayController {

    private final KafkaTemplate<String, PaymentEvent> kafkaTemplate;
    private final DlqMessageRepository dlqRepository;

    public DlqReplayController(KafkaTemplate<String, PaymentEvent> kafkaTemplate,
                               DlqMessageRepository dlqRepository) {
        this.kafkaTemplate = kafkaTemplate;
        this.dlqRepository = dlqRepository;
    }

    @PostMapping("/replay/{messageId}")
    public ResponseEntity<Map<String, Object>> replayDlqMessage(@PathVariable String messageId) {
        DlqMessage message = dlqRepository.findById(messageId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "DLQ message not found"));

        // Re-publish back to primary ingestion topic
        kafkaTemplate.send("payments.incoming", message.getPayload());
        dlqRepository.markAsReplayed(messageId);

        return ResponseEntity.ok(Map.of(
            "status", "REPLAYED",
            "messageId", messageId,
            "replayedAt", Instant.now().toString()
        ));
    }
}
```
