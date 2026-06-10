# API Documentation and Integration Guides

This document details developer specifications, rate limits, versioning updates, and troubleshooting checklists for the platform APIs.

## 1. API Versioning and Deprecation Timeline
* **v1 Sunset**: API version 1 is officially deprecated and scheduled to sunset on December 31, 2023. All integrations must migrate to API version 2 before this date.
* **v2 Breaking Changes**:
  * Mandatory headers structure updates (e.g. `X-Workspace-ID`).
  * Paginated responses by default.
  * Webhook cryptographic signature validation is required.

## 2. API Headers
All requests to API v2 endpoints must include the following headers:
* `Authorization`: `Bearer <API_KEY>`
* `X-Workspace-ID`: `<WORKSPACE_ID>` (Mandatory. Requests lacking this header will fail with HTTP 403 Forbidden).
* `Content-Type`: `application/json`

## 3. Rate Limits by Tier
API limits are enforced globally by IP and token signature:
* **Free Tier**: 60 requests/minute.
* **Standard Tier**: 1,000 requests/minute.
* **Pro Tier**: 2,500 requests/minute.
* **Enterprise Tier**: Custom limits starting at 5,000 requests/minute.
* **Rate Limit Upgrades**: Enterprise accounts may request rate limit increases through the support center. Custom ceilings require review by the Infrastructure Team and written approval from the Engineering Manager.

## 4. Webhook Security Requirements
Webhooks must include signature validation to prevent spoofing. The server sends the header `X-Hub-Signature-256` which is a HMAC-SHA256 signature generated using the client webhook secret key. Webhooks must be verified before processing.

## 5. Troubleshooting 403 Forbidden Errors
If an API client receives an HTTP 403 Forbidden error, go through the following steps:
1. Verify the `Authorization` header is present and the bearer token is valid.
2. Confirm the `X-Workspace-ID` header is included and matches the client's current workspace profile.
3. Check the endpoint permissions scope. Integrations configured for v1 scopes may hit 403 on v2 endpoints without a revised key scope.
