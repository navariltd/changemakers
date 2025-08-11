# Case API Endpoints

Base URL

- Live: [https://haki-na-sheria.navari.co.ke](https://haki-na-sheria.navari.co.ke)
- Staging Site: [https://staging-haki-na-sheria.m.frappe.cloud](https://staging-haki-na-sheria.m.frappe.cloud)

Authentication

- Requires an authenticated Frappe session.
  - Session: use the logged-in session cookie (sid).

- Access Authorization Cookies by logging in with user credentials.

Content Types

- POST with `application/json`.

---

## POST /api/method/login

Login to obtain an authorization token.

### Request

- Method: POST
- URL: `/api/method/login`
- Body Parameters:
  - `usr` (string, required) — the username
  - `pwd` (string, required) — the password

### Response

- `message` (string): Indicates the result of the login attempt. May be empty on successful login.
- `home_page` (string): URL of the home page the user will be redirected to after logging in. May be empty.
- `full_name` (string): Full name of the user. May also be empty.

Example successful response:

```json
{
    "message": "",
    "home_page": "/app/home",
    "full_name": "Jane Doe"
}
```

Authorization cookies will be set on response object on successful login.

Example failed response:

```json
{
    "message": "Invalid login credentials",
    "home_page": "",
    "full_name": ""
}
```


## POST /api/method/changemakers.api.issue.get_case

Retrieve a Case by the requestor’s ID number or phone number.

- Methods: POST
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
	"https://your-frappe-host/api/method/changemakers.api.issue.get_case?requestor_id=12345678" \
	-H "Authorization: token <api_key>:<api_secret>"
```

POST (JSON)

```bash
curl --location 'https://staging-haki-na-sheria.m.frappe.cloud/api/method/changemakers.api.issue.get_case' \
    --header 'Content-Type: application/json' \
    --header 'Cookie: full_name=<username>; sid=<sid retrieved from login>; system_user=yes; user_id=<user id set from login>; user_image=' \
    --data '{
        "requestor_phone": "793-583-4161"
    }'
```

Successful response

```json
{
  "message": {
    "success": true,
    "case_name": "CASE-0001",
    "status": "Open",
    "assigned_paralegals": [
      { "user": "paralegal1@example.com", "phone": "+254700000001" }
    ]
  }
}
```

Not found response

```json
{
  "message": {
    "success": false,
    "message": "No case found with the provided details."
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
  - `"'county' must be provided."`
  - `"'type' must be provided."`
- Invalid `birth_certificate_type`:
  - `"'birth_certificate_type' must be either 'New Born Registration' or 'Late Registration'."`

Example

```bash
curl -X POST \
	"https://your-frappe-host/api/method/changemakers.api.issue.create_case" \
	-H "Content-Type: application/json" \
	-H "Cookie: full_name=<username>; sid=<sid retrieved from login>; system_user=yes; user_id=<user id set from login>; user_image=" \
	-d '{
		"requestor_id": "12345678",
		"requestor_phone": "+254700000000",
		"description": "Birth certificate assistance required.",
		"county": "nairobi",
		"title": "legal identity help",
		"type": "birth certificate",
		"birth_certificate_type": "late registration",
		"requestor_service_rating": 4
	}'
```

Successful response

```json
{
  "message": {
    "success": true,
    "case_name": "CASE-0002",
    "case_title": "Legal Identity Help"
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
