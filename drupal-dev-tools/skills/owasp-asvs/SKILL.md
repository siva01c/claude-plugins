---
name: owasp-asvs
description: OWASP ASVS v5.0 security verification skill. Use when performing security code reviews or implementing security requirements.
---

# ASVS Security Verification Skill

Reference: OWASP ASVS v5.0.0 — cross-reference IDs against https://github.com/OWASP/ASVS for the authoritative source.

## When This Activates

- Performing security code reviews
- Implementing security features
- Responding to security review findings
- Security compliance verification

---

## ASVS Requirements Checklist

### V1 — Encoding and Sanitization (Critical)

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V1.1.1 | Output encoding for HTTP/HTML context | Twig auto-escape or `#plain_text` |
| V1.1.2 | Dynamic URL building with encoding | `Url::fromRoute()`, never string concat |
| V1.1.3 | JavaScript/JSON encoding | `Json::encode()` before output |
| V1.1.4 | **SQL injection prevention** | **Parameterized queries only** |
| V1.1.5 | OS command injection prevention | Avoid `shell_exec`, `exec`, `system` |
| V1.1.6 | LDAP injection prevention | Use parameterized LDAP queries |
| V1.1.7 | Regex metacharacter escaping | `preg_quote()` on user input |
| V1.2.1 | HTML sanitization | `Xss::filter()` or `Xss::filterAdmin()` |
| V1.2.2 | No `eval()` with user input | Avoid `eval()`, use `Json::decode()` |
| V1.2.3 | SSRF prevention | Validate URLs against explicit allowlist |

### V2 — Validation

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V2.1.1 | Input validation at server | Validate all user input server-side |
| V2.1.2 | Server-side validation only | Never trust client-only validation |
| V2.2.1 | Positive validation (allowlist) | Use `\Drupal\Component\Utility\Html::escape()` for plain text |
| V2.3.1 | **Anti-automation / rate limiting** | Flood control or custom rate limit service |

### V3 — Web Frontend Security

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V3.1.1 | Cookie Secure attribute | `ini_set('session.cookie_secure', TRUE)` |
| V3.1.2 | Cookie SameSite attribute | `session.cookie_samesite = Lax` in `settings.php` |
| V3.1.3 | Cookie HttpOnly | `session.cookie_httponly = TRUE` |
| V3.2.1 | **HSTS header** | `Strict-Transport-Security` response header |
| V3.2.2 | **CORS allowlist** | **Validate Origin; never use wildcard** |
| V3.2.3 | CSP header | `Content-Security-Policy` response header |
| V3.2.4 | X-Content-Type-Options | `nosniff` |
| V3.2.5 | Referrer-Policy | Set appropriate policy |
| V3.2.6 | frame-ancestors | Prevent clickjacking via CSP or `X-Frame-Options` |
| V3.3.1 | **CSRF protection** | Form API tokens (automatic) or `CsrfTokenGenerator` for custom endpoints |

### V4 — API and Web Service

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V4.1.1 | Content-Type header | Set correct `Content-Type` on all responses |
| V4.1.2 | HTTP method restrictions | `routing.yml` `methods:` key |
| V4.1.3 | HTTP request smuggling | Proper header parsing; avoid custom HTTP parsing |
| V4.2.1 | Authentication on every API endpoint | `_permission` or `_custom_access` in routing |

### V5 — File Handling

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V5.1.1 | File size limits | `upload_max_filesize`, managed file field limits |
| V5.1.2 | File type validation | `file_validate_extensions()` + MIME check |
| V5.2.1 | No file execution | Never serve uploads from a web-accessible path as PHP |
| V5.2.2 | Path traversal prevention | Use `FileSystem::realpath()`, validate against allowed dirs |

### V6 — Authentication

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V6.1.1 | Password minimum length | Minimum 12 chars (Drupal default: 8 — raise it) |
| V6.1.2 | Breached password check | Integrate HaveIBeenPwned API or `password_policy` module |
| V6.1.3 | No restrictive composition rules | Allow all printable characters |
| V6.1.4 | Long password support | Allow 64+ characters |
| V6.2.1 | Multi-factor authentication | `tfa` module or SAML/OIDC with MFA |
| V6.3.1 | **Secrets from secure source** | `getenv()` or Key module — never `config.get()` |
| V6.3.2 | No production secret fallback | Throw exception if secret missing in prod |

### V7 — Session Management

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V7.1.1 | Session identifier length | Minimum 128 bits of entropy |
| V7.1.2 | Session identifier randomness | Cryptographically random (Drupal core handles this) |
| V7.1.3 | Session inactivity timeout | Configure in `settings.php` |
| V7.1.4 | Session termination on logout | `session_destroy()` via `AccountInterface::logout()` |
| V7.2.1 | New session on privilege change | `\Drupal::service('session')->migrate()` on role change |
| V7.2.2 | Session token not in URLs | Ensure `session.use_only_cookies = TRUE` |

### V8 — Authorization

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V8.1.1 | Least privilege | Grant minimal roles/permissions |
| V8.1.2 | Role-based access control | `user.permissions` + `AccessResult` |
| V8.1.3 | Access control on every request | `_permission`, `_entity_access`, or `_custom_access` |
| V8.2.1 | No user/role enumeration | Return identical responses for missing vs forbidden |
| V8.2.2 | Sensitive data access logging | Watchdog or event subscriber |
| V8.3.1 | Object-level authorization | Check entity ownership, not just route access |

### V9 — Communication (TLS/Transport)

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V9.1.1 | TLS required for all traffic | Enforce HTTPS; redirect HTTP → HTTPS |
| V9.1.2 | TLS certificate validity | Valid cert, no self-signed in production |
| V9.1.3 | TLS 1.2+ only | Disable TLS 1.0/1.1 at server level |
| V9.2.1 | No mixed content | Serve all assets over HTTPS |
| V9.3.1 | Outbound TLS verification | Verify peer cert in `\GuzzleHttp\Client` calls |

### V10 — Malicious Code / Supply Chain

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V10.1.1 | Dependency integrity | `composer.lock` committed; use `composer audit` |
| V10.1.2 | No unused dependencies | Regularly prune `composer.json` |
| V10.2.1 | Code review for third-party modules | Review contrib module code before enabling |
| V10.3.1 | Integrity verification | Use `drupal/core-recommended` and check module checksums |

### V11 — Business Logic

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V11.1.1 | Sequential step enforcement | Enforce workflow states server-side |
| V11.1.2 | Business logic limits | Rate limits per user/IP per operation |
| V11.1.3 | Transaction handling | Use `\Drupal\Core\Database\Connection::startTransaction()` |

### V12 — Configuration

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V12.1.1 | Debug mode disabled | `$settings['twig_debug'] = FALSE` in prod |
| V12.1.2 | Verbose errors suppressed | `error_reporting(0)` in prod; use logging |
| V12.1.3 | Security headers present | HSTS, CSP, X-Content-Type-Options |
| V12.2.1 | Remove unused modules | Uninstall and remove unused contrib |
| V12.3.1 | Protect sensitive config files | `.htaccess` on `sites/default/`, `settings.php` read-only |

### V13 — Data Protection

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V13.1.1 | Sensitive data not logged | Strip PII from watchdog/log entries |
| V13.1.2 | Sensitive data not in URLs | Never pass tokens or PII as query parameters |
| V13.2.1 | Data retention policy | Define and enforce data retention in code |
| V13.3.1 | Alert on anomalies | Event subscriber for suspicious patterns |

### V14 — Cryptography

| ID | Requirement | Drupal Validation |
|----|-------------|-------------------|
| V14.1.1 | Approved algorithms only | AES-256, SHA-256+; no MD5/SHA-1 for security |
| V14.2.1 | Secure random number generation | `\Drupal\Component\Utility\Crypt::randomBytes()` |
| V14.3.1 | Passwords hashed with strong algorithm | Drupal's `PhpassHashedPassword` (or stronger via `password_compat`) |
| V14.4.1 | Secrets not in source code | Key module or environment variables |
| V14.5.1 | No hardcoded crypto keys | Use Key module; rotate keys on breach |

---

## Critical Security Patterns for Drupal

### SQL Injection (V1.1.4)

```php
// VULNERABLE
$query = "SELECT * FROM users WHERE name = '" . $name . "'";

// SAFE — Drupal Query Builder
$result = $this->connection->select('users', 'u')
  ->fields('u')
  ->condition('name', $name)
  ->execute();

// SAFE — Placeholder
$result = $this->connection->query(
  'SELECT * FROM {users} WHERE name = :name',
  [':name' => $name]
);
```

### XSS Prevention (V1.2.1)

```php
// VULNERABLE
['#markup' => $user_input]

// SAFE — plain text
['#plain_text' => $user_input]

// SAFE — Twig auto-escape (always prefer)
{{ variable }}

// SAFE — Admin HTML (trusted editors only)
use Drupal\Component\Utility\Xss;
$safe = Xss::filterAdmin($html);

// SAFE — plain text in arbitrary context
use Drupal\Component\Utility\Html;
$safe = Html::escape($user_input);
```

### CORS Configuration (V3.2.2)

```php
// VULNERABLE — wildcard
$response->headers->set('Access-Control-Allow-Origin', '*');

// SAFE — explicit allowlist; only add Credentials header when the
// endpoint actually requires cookie/auth-header sharing
$allowed = $config->get('allowed_origins') ?: [];
$origin = $request->headers->get('Origin', '');
if ($origin && in_array($origin, $allowed, TRUE)) {
  $response->headers->set('Access-Control-Allow-Origin', $origin);
  $response->headers->set('Vary', 'Origin');
  // Only add if this endpoint specifically requires credentialed requests:
  // $response->headers->set('Access-Control-Allow-Credentials', 'true');
}
```

### Authorization — Entity Access (V8.1.3, V8.3.1)

```php
// VULNERABLE — route access only, no object-level check
$node = Node::load($nid);
return $node->get('field_secret')->value;

// SAFE — always check entity access
$node = Node::load($nid);
if (!$node || !$node->access('view')) {
  throw new AccessDeniedHttpException();
}
return $node->get('field_secret')->value;

// SAFE — AccessResult in access checker service
use Drupal\Core\Access\AccessResult;
public function access(AccountInterface $account): AccessResult {
  return AccessResult::allowedIfHasPermission($account, 'view secret content')
    ->cachePerPermissions();
}
```

### CSRF for Custom Endpoints (V3.3.1)

```php
// VULNERABLE — custom route with no CSRF check
public function myAction(Request $request): Response { ... }

// SAFE — Form API handles CSRF automatically; for non-form endpoints:
// In routing.yml add: requirements: { _csrf_token: 'TRUE' }
// Then validate token in controller:
$token = $request->query->get('token');
if (!$this->csrfTokenGenerator->validate($token, 'my-action')) {
  throw new AccessDeniedHttpException();
}
```

### Rate Limiting — Flood Control (V2.3.1)

```php
// Drupal's built-in flood control service
$flood = \Drupal::service('flood');
$identifier = $request->getClientIp();

if (!$flood->isAllowed('my_module.action', $threshold = 10, $window = 3600, $identifier)) {
  throw new TooManyRequestsHttpException(null, 'Rate limit exceeded.');
}

// Register the flood event after processing
$flood->register('my_module.action', $window = 3600, $identifier);
```

### Secret Management (V6.3.1)

```php
// VULNERABLE — stored in config
$secret = $config->get('jwt_secret');

// SAFE — environment variable
$secret = getenv('JWT_SECRET');

// SAFE — Key module (preferred for Drupal)
$key = \Drupal::service('key.repository')->getKey('jwt_secret');
$secret = $key->getKeyValue();

// Always fail hard in production if secret is missing
if ($is_production && empty($secret)) {
  throw new \RuntimeException('JWT secret is required in production.');
}
```

### Security Headers (V3.2.1–V3.2.4)

```php
// In an EventSubscriber on KernelEvents::RESPONSE:
$response->headers->set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
$response->headers->set('X-Content-Type-Options', 'nosniff');
$response->headers->set('Content-Security-Policy', "default-src 'self'; script-src 'self'");
$response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
$response->headers->set('X-Frame-Options', 'SAMEORIGIN');
```

### File Upload Validation (V5.1.2)

```php
// SAFE — validate extension and MIME type
$validators = [
  'file_validate_extensions' => ['pdf jpg png'],
  'file_validate_size'       => [10 * 1024 * 1024], // 10 MB
  'file_validate_image_resolution' => ['2000x2000'],
];
$file = file_save_upload('my_field', $validators, 'private://', FILE_EXISTS_RENAME);
if (!$file) {
  // Upload failed validation
}
```

### Cryptographic Operations (V14.2.1, V14.3.1)

```php
// SAFE — cryptographically secure random bytes
use Drupal\Component\Utility\Crypt;
$token = Crypt::randomBytesBase64(32);

// SAFE — password hashing (Drupal core)
$hashed = \Drupal::service('password')->hash($plain);
$valid  = \Drupal::service('password')->check($plain, $hashed);

// UNSAFE — never use for security-sensitive hashing
$bad = md5($input);
$bad = sha1($input);
```

---

## Quick Verification Checklist

Before any code is committed:

- [ ] **V1.1.4** SQL uses parameterized queries (Query Builder or placeholders)
- [ ] **V1.2.1** Output uses `#plain_text`, `Html::escape()`, or Twig auto-escape
- [ ] **V3.2.2** CORS uses explicit allowlist — no `*`
- [ ] **V3.2.3** CSP header defined and restrictive
- [ ] **V3.2.1** HSTS enforced for all HTTPS traffic
- [ ] **V3.3.1** CSRF tokens present (Form API or `_csrf_token` routing requirement)
- [ ] **V2.3.1** Rate limiting via flood control on sensitive endpoints
- [ ] **V6.3.1** Secrets from Key module or environment — not from `config.get()`
- [ ] **V7.1.4** Session destroyed on logout
- [ ] **V8.1.3** Entity access checked on every object load (not just route)
- [ ] **V9.1.1** All traffic over TLS; HTTP redirects to HTTPS
- [ ] **V10.1.1** `composer audit` passes; `composer.lock` committed
- [ ] **V12.1.1** Debug/verbose error modes disabled in production
- [ ] **V14.1.1** No MD5/SHA-1 for security-sensitive operations

---

## Red Flags

| Pattern | ASVS | Risk |
|---------|------|------|
| String concat in SQL | V1.1.4 | SQL injection |
| `#markup` with user data | V1.2.1 | XSS |
| `Access-Control-Allow-Origin: *` | V3.2.2 | Cross-origin data leakage |
| `eval()` with input | V1.2.2 | Code injection |
| `config.get()` for secrets | V6.3.1 | Credential exposure |
| No rate limiting on auth/forms | V2.3.1 | Brute force / DoS |
| Missing CSRF token | V3.3.1 | CSRF |
| No entity access check | V8.3.1 | Broken object-level auth |
| MD5/SHA-1 for passwords or tokens | V14.1.1 | Weak cryptography |
| Uploaded files in public:// without type check | V5.1.2 | Remote code execution |
| HTTP-only routes in production | V9.1.1 | Credential interception |
| Debug mode / verbose errors in prod | V12.1.1 | Information disclosure |

---

## Drupal-Specific Module References

| Concern | Recommended Module / Core API |
|---------|-------------------------------|
| Secrets / key storage | `drupal/key` + `drupal/key_asymmetric` |
| Rate limiting | Core Flood service or `drupal/rate_limiter` |
| MFA | `drupal/tfa` |
| Password policy | `drupal/password_policy` |
| Security headers | `drupal/seckit` |
| SAML / OIDC SSO | `drupal/samlauth` or `drupal/openid_connect` |
| File scanning | `drupal/clamav` |
| Security audit | `drupal/security_review` |
| Dependency audit | `composer audit` (built-in) |

---

## References

- [OWASP ASVS v5.0](https://owasp.org/www-project-application-security-verification-standard/)
- [ASVS v5.0 GitHub (authoritative IDs)](https://github.com/OWASP/ASVS)
- [Drupal Security Documentation](https://www.drupal.org/docs/security-in-drupal)
- [Drupal Secure Coding Standards](https://www.drupal.org/docs/security-in-drupal/writing-secure-code-for-drupal)
