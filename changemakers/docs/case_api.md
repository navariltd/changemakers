# Case API Endpoints

Base URL

- Live: [https://haki-na-sheria.navari.co.ke](https://haki-na-sheria.navari.co.ke)
- Staging Site: [https://staging-haki-na-sheria.m.frappe.cloud](https://staging-haki-na-sheria.m.frappe.cloud)

Authentication

- Requires an authenticated API Key.

Content Types

- POST/GET with `application/json`.

---

## How to Generate User API Key

1. Log in to the Haki na Sheria platform.
2. Select your user profile.
3. Click on "My Settings".
4. Click on "Generate API Key".
5. Copy the generated API key and keep it secure.

---

## GET /api/method/changemakers.api.issue.get_case

Retrieve a Case by the requestor’s ID number or phone number.

- Methods: GET
- URL: `/api/method/changemakers.api.issue.get_case`
- Auth: Required

Parameters

- `requestor_id` (string, optional)
- `requestor_phone` (string, optional)
- At least one of `requestor_id` or `requestor_phone` must be provided.

Response (200 OK)

- `success` (boolean)
- `message` (string, optional) — present if not found or input invalid
- `case_name` (string, optional)
- `status` (string, optional) — returns "Open" if stored status is "New"; otherwise the stored status
- `assigned_paralegals` (array, optional)
  - Items: `{ "user": string, "phone": string }`

Validation and Behavior

- If both identifiers are missing: `success=false` with a message.
- If no matching case: `success=false` with a message.
- If found: `success=true` with case details; `assigned_paralegals` array may be empty if no paralegal is assigned to the case.

Examples

GET (query string)

```bash
curl -X GET \
    "BASE_URL/api/method/changemakers.api.issue.get_case?requestor_id=12345678" \
    -H "Authorization: token <api_key>:<api_secret>"
```

GET (JSON)

```bash
curl --location 'https://staging-haki-na-sheria.m.frappe.cloud/api/method/changemakers.api.issue.get_case' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: token <api_key>:<api_secret>' \
    --data '{
        "requestor_phone": "712345678"
    }'
```

Successful response

```json
{
  "message": {
    "success": true,
    "case_name": "8001",
    "status": "Open",
    "assigned_paralegals": [
      { "user": "paralegal1@example.com", "phone": "+254700000001" }
    ]
  }
}
```

Invalid input response

```json
{
  "message": {
    "success": false,
    "message": "Either 'requestor_id' or 'requestor_phone' must be provided."
  }
}
```

---

## POST /api/method/changemakers.api.issue.create_case

Create a new Case for a birth certificate request.

- Method: POST
- URL: `/api/method/changemakers.api.issue.create_case`
- Auth: Required

Body Parameters

- `requestor_id` (string, required)
- `requestor_phone` (string, required)
- `description` (string, required)
- `county` (string, required) — title-cased on save
- `title` (string, required) — title-cased on save
- `type` (string, required) — title-cased on save
- `birth_certificate_type` (string, required) — one of:
  - `"New Born Registration"`
  - `"Late Registration"`
  - Value is title-cased before validation
- `requestor_service_rating` (integer, optional) — defaults to `0` when omitted

Behavior

- New cases are created with `status` set to `"New"`.
- To read the current status after creation, use `get_case` (note: `"New"` is surfaced as `"Open"`).

Response (200 OK)

- `success` (boolean)
- `message` (string, optional) — present on validation failure
- `case_name` (string, optional) — on success
- `case_title` (string, optional) — on success

Validation errors (examples)

- Missing fields:
  - `"'requestor_id' or 'requestor_phone' must be provided."` (both are required in practice)
  - `"'title' must be provided."`
  - `"'county' must be provided and must be included in the system's County list."`
  - `"'type' must be provided and must always be 'Civil Case'."`
- Invalid `birth_certificate_type`:
  - `"'birth_certificate_type' must be either 'New Born Registration' or 'Late Registration'."`

Example

```bash
curl -X POST \
    "BASE_URL/api/method/changemakers.api.issue.create_case" \
    -H "Content-Type: application/json" \
    -H "Authorization: token <api_key>:<api_secret>" \
    -d '{
        "requestor_id": "12345678",
        "requestor_phone": "+254700000000",
        "description": "Birth certificate assistance required.",
        "county": "nairobi",
        "title": "legal identity help",
        "type": "Civil Case",
        "birth_certificate_type": "late registration",
        "requestor_service_rating": 4
    }'
```

Successful response

```json
{
  "message": {
    "success": true,
    "case_name": "132",
    "status": "Open",
    "type": "Civil Case",
    "assigned_paralegals": [
      { "full_name": "Paralegal One", "phone": "+254700000001" },
      { "full_name": "Paralegal Two", "phone": "+254700000002" }
    ]
  }
}
```

Validation failure response

```json
{
  "message": {
    "success": false,
    "message": "'birth_certificate_type' must be either 'New Born Registration' or 'Late Registration'."
  }
}
```
