# Operations Escalation Matrix

This document outlines team routing mappings and safety rules regarding automated messaging actions.

## 1. Routing Queues and Ownership
Incoming tickets and customer cases must be routed to specialized departments based on subject matter:

* **Legal Threats**:
  * **Keywords**: Lawsuit, attorney, cease and desist, trademark, legal action.
  * **Routing**: Route immediately to the **Legal Team**.
* **Security & Ransomware Extortion**:
  * **Keywords**: Ransomware, dark web, send 2 btc, exfiltrated, breach.
  * **Routing**: Route immediately to the **Security Incident Response Team**.
* **GDPR Portability / Article 20 Requests**:
  * **Keywords**: GDPR, Article 20, data portability, personal data export.
  * **Routing**: Route immediately to the **Compliance and Legal Operations Team**.
* **Public Reputation Threats**:
  * **Keywords**: Negative reviews, Trustpilot, Capterra, Twitter, G2.
  * **Routing**: Route immediately to the **Customer Success Lead**.
* **VIP Churn Threats**:
  * **Keywords**: VIP status, canceling subscription, account value > $10,000.
  * **Routing**: Route to the assigned **Account Executive** and the **Support Lead**.
* **P0 Outage / SLA Breach**:
  * **Keywords**: Production down, outage, downtime SLA.
  * **Routing**: Route immediately to the **Support Lead** and the **Engineering Manager**.
* **RFP and Security Questionnaire Audits**:
  * **Keywords**: RFP questionnaire, ISO 27001 audit, SOC 2 checklist.
  * **Routing**: Route to **Sales Engineering** and **Compliance Operations**.

## 2. Safety Policies and Automated Messaging Rules
To prevent brand damage and legal complications, standard automation rules are modified for critical cases:

* **Ransomware / Extortion Attacks**:
  * **Rule**: **NEVER auto-reply** under any circumstances. No auto-acknowledgments, no automatic tickets creation notifications. Disable all auto-responder templates immediately.
* **Legal Cease & Desist Notices / Threats**:
  * **Rule**: **NEVER auto-reply** without explicit, written human approval from the Legal Team. All automated responses must be suppressed.
* **GDPR Data Portability / Privacy Requests**:
  * **Rule**: **NEVER send generic auto-replies** or standard policy responses. Any response must be tailored, policy-grounded, and state the statutory timeline (30 days) explicitly.
