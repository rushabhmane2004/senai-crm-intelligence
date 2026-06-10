# Service Level Agreement (SLA) Policy

This document outlines the performance, uptime, support response target metrics, and SLA breach credit policies.

## 1. Uptime SLA Commitments
* The platform commits to a **99.9% system uptime** service availability in any billing calendar month, excluding scheduled maintenance windows (scheduled at least 48 hours in advance during off-peak hours).

## 2. Incident Classifications and Response Targets
* **P0 (Critical Outage)**: System is completely down or severely degraded for all or a majority of users. No workaround is available.
  * **Initial Response Target**: 15 minutes.
  * **Resolution Target**: 4 hours.
  * **Root Cause Analysis (RCA)**: A formal written RCA report must be delivered to the client within 24 hours of incident resolution.
* **P1 (High Severity)**: Core features (e.g. email ingestion, reporting dashboard) are degraded, causing major business impact.
  * **Initial Response Target**: 1 hour.
  * **Resolution Target**: 12 hours.

## 3. SLA Credit Calculations & Downtime Eligibility
* In the event that uptime falls below 99.9% during a billing cycle, Enterprise clients are eligible to apply for downtime service credits.
* **Credit Tiers**:
  * Uptime < 99.9% but >= 99.0%: 10% credit of the monthly subscription fee.
  * Uptime < 99.0% but >= 95.0%: 25% credit of the monthly subscription fee.
  * Uptime < 95.0%: 50% credit of the monthly subscription fee.
* **Eligibility Rules**: Claims must be submitted within 14 business days of the incident. Credits are applied to future invoices only and cannot be converted to cash refunds.

## 4. Escalation Path for SLA Breaches
* If resolution targets are breached for P0 incidents, the escalation path is:
  1. Support Lead -> notified immediately at target breach.
  2. Engineering Manager -> notified at T+1 hour past target.
  3. VP of Engineering + Chief Customer Officer -> notified at T+2 hours past target.
* All SLA breaches must be flagged in the CRM to notify the corresponding Account Executive and Support Lead to address churn and renewal-risk handling.
