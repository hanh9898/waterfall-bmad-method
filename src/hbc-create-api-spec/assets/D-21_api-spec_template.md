---
document_id: D-21
title: "{project_name} API仕様書"
version: "1.0"
api_style: "REST"
status: draft
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} API仕様書 (API Specification)

## 1. 概要 (Overview)

### 1.1 目的 (Purpose)

<!-- Purpose and scope of this API -->

### 1.2 ベースURL (Base URL)

| Environment | Base URL |
|-------------|----------|

### 1.3 バージョニング (Versioning)

<!-- API versioning strategy: path-based (/v1/), header-based, query param -->

## 2. 認証・認可 (Authentication & Authorization)

### 2.1 認証方式 (Authentication Method)

<!-- JWT, API Key, OAuth2, Session — describe the mechanism -->

### 2.2 トークンライフサイクル (Token Lifecycle)

<!-- Issuance, refresh, expiration, revocation -->

### 2.3 権限モデル (Permission Model)

<!-- Roles, scopes, permission matrix -->

## 3. 共通仕様 (Common Specifications)

### 3.1 リクエストフォーマット (Request Format)

<!-- Content-Type, charset, common headers -->

### 3.2 レスポンスフォーマット (Response Format)

<!-- Standard envelope structure -->

```json
{
  "status": "success | error",
  "data": {},
  "error": {
    "code": "string",
    "message": "string"
  },
  "meta": {
    "total": 0,
    "page": 1,
    "limit": 20
  }
}
```

### 3.3 ページネーション (Pagination)

<!-- Pagination strategy: offset-based, cursor-based -->

### 3.4 エラーコード (Error Codes)

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|

## 4. エンドポイント一覧 (Endpoint List)

| # | Method | Endpoint | Description | REQ ID |
|---|--------|----------|-------------|--------|

## 5. エンドポイント詳細 (Endpoint Details)

<!-- Repeat this block for each endpoint -->

### 5.x {endpoint_name}

**Method:** `GET | POST | PUT | PATCH | DELETE`
**URL:** `/api/v1/{resource}`
**Description:**
**Requirements:** REQ-xxx
**Authentication:** Required | Optional | None

#### Request

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|

#### Request Body

```json
{}
```

#### Response (Success)

```json
{}
```

#### Response (Error)

```json
{}
```

#### Notes

<!-- Edge cases, business rules, rate limits -->

## 6. データモデル (Data Models)

<!-- Shared schema definitions referenced across endpoints -->

### 6.1 {model_name}

| Field | Type | Required | Description |
|-------|------|----------|-------------|

## 7. レート制限 (Rate Limiting)

<!-- Rate limiting strategy, per-endpoint limits if applicable -->

| Scope | Limit | Window |
|-------|-------|--------|

## 改訂履歴 (Revision History)

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
