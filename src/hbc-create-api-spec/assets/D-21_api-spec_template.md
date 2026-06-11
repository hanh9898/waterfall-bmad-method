---
document_id: D-21
title: "{project_name} — Đặc tả API"
version: "1.0"
api_style: "REST"
status: draft
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — Đặc tả API (API Specification)

## 1. Tổng quan (Overview)

### 1.1 Mục đích (Purpose)

<!-- Purpose and scope of this API -->

### 1.2 Base URL

| Environment | Base URL |
|-------------|----------|

### 1.3 Phiên bản hóa (Versioning)

<!-- API versioning strategy: path-based (/v1/), header-based, query param -->

## 2. Xác thực & phân quyền (Authentication & Authorization)

### 2.1 Phương thức xác thực (Authentication Method)

<!-- JWT, API Key, OAuth2, Session — describe the mechanism -->

### 2.2 Vòng đời token (Token Lifecycle)

<!-- Issuance, refresh, expiration, revocation -->

### 2.3 Mô hình phân quyền (Permission Model)

<!-- Roles, scopes, permission matrix -->

## 3. Quy cách chung (Common Specifications)

### 3.1 Định dạng request (Request Format)

<!-- Content-Type, charset, common headers -->

### 3.2 Định dạng response (Response Format)

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

### 3.3 Phân trang (Pagination)

<!-- Pagination strategy: offset-based, cursor-based -->

### 3.4 Mã lỗi (Error Codes)

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|

## 4. Danh sách endpoint (Endpoint List)

| # | Method | Endpoint | Description | REQ ID |
|---|--------|----------|-------------|--------|

## 5. Chi tiết endpoint (Endpoint Details)

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

## 6. Mô hình dữ liệu (Data Models)

<!-- Shared schema definitions referenced across endpoints -->

### 6.1 {model_name}

| Field | Type | Required | Description |
|-------|------|----------|-------------|

## 7. Giới hạn tần suất (Rate Limiting)

<!-- Rate limiting strategy, per-endpoint limits if applicable -->

| Scope | Limit | Window |
|-------|-------|--------|

## Lịch sử sửa đổi (Revision History)

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
