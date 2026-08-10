# MBS Registration — Standalone Web App Specification

A build brief for replacing the two Frappe-hosted registration pages (`/mbreg1825`
and `/apply-dd`) with a standalone web app that talks to the existing Frappe
backend over its REST API.

**Give this file to a fresh Claude Code instance in a new, empty repository.**
It contains everything about the current system needed to rebuild it — nothing
in this document requires reading the `education` app source.

---

## 1. Why this exists

Today both registration forms are Vue 3 pages served by Frappe from
`education/www/*.html`. Every change requires a Frappe deploy, and a deploy that
fails part-way (a bad patch, a schema conflict) rolls back and leaves the pages
stale. There is also a Desk override feature that, when switched on, silently
freezes a page at whatever HTML was saved — deploys stop reaching it entirely.

The goal: the forms become an ordinary web app, deployed independently (e.g.
Cloudflare Pages + Workers), released in seconds, while Frappe stays as the
system of record.

### Scope

Rebuild, at feature parity:

| Current page | Purpose | Audience |
|---|---|---|
| `/mbreg1825` | Main + MBS #2 registration, New and Existing students | Public/staff |
| `/apply-dd` | MBS Dembi Dollo registration | Login + `DD Student Registrar` role |

Plus these read-only staff views, currently separate pages worth folding in:
`/student-ids` (all generated IDs), `/paid-applicants` (paid applicants).

---

## 2. Architecture — read this before writing any code

### 2.1 The credential model must not be what you might first reach for

The original idea was: *"store a list of acceptable API keys and secrets in the
code for specific people."*

**Do not do this.** Anything in a browser bundle is public — view-source, the
network tab, or the deployed JS on Cloudflare Pages all expose it. Embedding
Frappe API secrets client-side hands full API access, for every one of those
users, to anyone who opens the page. Frappe API keys are not scoped per
endpoint; a leaked secret can read and write every doctype that user can.

Use this instead:

```
Browser (Cloudflare Pages, static)
    |  session cookie (HttpOnly, SameSite=Strict)
    v
Cloudflare Worker  ← the ONLY holder of Frappe credentials
    |  Authorization: token <api_key>:<api_secret>   (Worker Secret)
    v
Frappe REST API (app.makkobillischool.com)
```

- The Worker holds **one service account's** key/secret, stored as a Worker
  Secret (`wrangler secret put FRAPPE_API_SECRET`). It never reaches the browser.
- Users authenticate to the **Worker**, not to Frappe. Simplest workable scheme:
  a short allowlist of staff accounts with Argon2/bcrypt password hashes in a D1
  table or KV, issuing a signed session JWT (HttpOnly cookie, ~12h).
- The Worker enforces **roles** (`registrar`, `dd_registrar`, `viewer`) and
  refuses any request outside the caller's role before it ever reaches Frappe.
- The Worker exposes only the narrow set of operations in §4 — never a generic
  "proxy anything to Frappe" endpoint, which would just relocate the problem.

If per-person Frappe attribution matters (so the Frappe `owner` field shows who
registered a student), give each staff member their own Frappe API key, store
those **in the Worker's secret store keyed by user id**, and have the Worker
select the right one after authenticating the session. Credentials still never
reach the browser.

### 2.2 Suggested stack

- **Frontend**: React or Vue 3 + Vite + TypeScript, Tailwind. The current pages
  are Vue 3 via CDN with a single `createApp({...})` — porting the logic is
  mechanical.
- **Backend-for-frontend**: Cloudflare Worker (Hono works well).
- **Session/state**: Cloudflare D1 (users, sessions, audit log) + KV (rate limits).
- **Hosting**: Cloudflare Pages for the SPA, Worker on a route like
  `/api/*` on the same domain so the cookie is first-party.

---

## 3. Frappe backend contract

Base URL: `https://app.makkobillischool.com`

Authentication header the Worker sends on every call:

```
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
Accept: application/json
```

Frappe whitelisted methods are called as:

```
POST /api/method/<dotted.path.to.method>
Body: {"arg_name": value, ...}
Response: {"message": <return value>}
```

Generic doctype REST (useful for the read-only lists) is:

```
GET /api/resource/Student%20Applicant?filters=[["branch","=","Main"]]&fields=["name","first_name"]&limit_page_length=200
```

### 3.1 Frappe error shape — this matters for §7

A thrown error comes back as HTTP 417/500 with:

```json
{
  "exc_type": "ValidationError",
  "exception": "frappe.exceptions.ValidationError: <message>",
  "exc": "[\"Traceback (most recent call last):\\n ...\"]",
  "_server_messages": "[\"{\\\"message\\\": \\\"Human readable text\\\", \\\"title\\\": \\\"Message\\\"}\"]"
}
```

**The user-facing reason lives in `_server_messages`** — a JSON string containing
an array of JSON strings, each with a `message` key that may contain HTML. Code
that only reads `message` or `exc` will show nothing useful. This exact mistake
is why the current pages report "Please try again in a moment" for every failure.

Parse in this order: `_server_messages[].message` (strip HTML) → `exception` →
`exc` last frame → `HTTP status + statusText`.

---

## 4. Endpoints the app needs

All are `education.education.api.*` unless noted. Marked **guest** where the
current backend allows unauthenticated calls (the Worker should still require a
session).

### Registration flow

| Method | Args | Returns | Notes |
|---|---|---|---|
| `generate_school_id` | `branch` = `"M1"` \| `"M2"` | `"M1/48213/19"` | guest. Random 10001–99999, checked unique against Student **and** Student Applicant |
| `generate_dd_school_id` | — | `"MB/DD/48213/19"` | **Requires `DD Student Registrar` role** |
| `create_guardian` | `guardian_data` (§5.3) | Guardian docname | guest. Upserts by `mobile_number` |
| `create_student_application` | `application_data` (§5.1) | Applicant docname | guest. Main creation path |
| `submit_existing_student_application` | `application_data` | `{name, custom_school_id, branch}` | Updates the Student in place, then files the applicant. **Currently broken — see §9.1** |
| `get_existing_student_details` | `school_id` | profile + promotion decision (§5.4) | Existing-student lookup |
| `check_duplicate_application` | `mobile_number` / school id | duplicate info | Not used on `/apply-dd` by design (one guardian, many children) |
| `search_student_by_school_id` | `school_id` | Student or Applicant summary | |
| `upload_file_guest` | multipart `file`, `is_private=0`, `folder` | `{file_url}` | guest. **multipart/form-data, not JSON** |
| `validate_phone_number` | `phone_number` | validity | Client-side regex is enough; see §6.4 |

### Reference data

| Method | Returns |
|---|---|
| `get_programs_for_application` | Programs selectable on the form |
| `get_academic_years` | Academic Year list |
| `get_education_levels` | Guardian education options |
| `get_occupation_options` | Guardian occupation options |
| `get_kebele_subcity_data` | Sub-city → kebele map (Adama/Main only; DD uses free-text kebele) |
| `get_next_program` | Promotion target for a program |
| `suggest_student_section` | `program`, `gender`, `prev_section` → Student Group |

### Staff / read-only views

| Method | Args | Returns |
|---|---|---|
| `get_dd_applied_students` | `search`, `limit` | Dembi Dollo applicants + computed `age`, `paid` |
| `get_generated_ids` | `search`, `branch`, `applicant_type`, `limit` | All applicants with School IDs |
| `get_paid_applicants` | `search`, `branch`, `limit` | Applicants with `paid = 1` |

These three call `_require_staff()`, which allows: `System Manager`,
`Academics User`, `Education Manager`, `DD Student Registrar`, `Accounts Manager`,
`Accounts User`.

### Documents

| Method | Args | Notes |
|---|---|---|
| `generate_application_pdf` | `application_id` | App-specific PDF |
| `frappe.utils.print_format.download_pdf` | `doctype`, `name`, `format`, `no_letterhead` | Frappe built-in |

### Push notifications (existing, reusable)

`education.api.push_notifications.*`:
`register_device_token(push_token, device_type, app_version, device_model)`,
`get_notifications_for_user(limit, offset)`, `mark_notification_as_read(notification_id)`,
`get_notification_categories()`, `test_push_notification()`.

> **Bug to avoid inheriting:** the `Push Token` doctype declares `push_token` as
> `unique: 1`, but no unique index exists in the database and there are 610
> duplicate tokens — one registered 78 times, so those devices receive 78 copies
> of every notification. Deduplicate by `(user, push_token)` before registering.

---

## 5. Data model

### 5.1 `application_data` payload for `create_student_application`

```jsonc
{
  "first_name": "Abel",              // required — student's own name
  "middle_name": "Tesfaye",          // father's name
  "last_name": "Bekele",             // grandfather's name
  "date_of_birth": "2015-04-12",     // ISO, Gregorian (convert from Ethiopian first)
  "gender": "Male",                  // "Male" | "Female" (Link → Gender)
  "program": "Grade 3 AO",           // required, Link → Program
  "academic_year": "2019 E.C.",      // required, Link → Academic Year
  "custom_school_id": "M1/48213/19", // from generate_school_id / generate_dd_school_id
  "student_email_id": "",            // leave empty — server derives it, see §6.2
  "applicant_type": "New",           // "New" | "Existing"
  "branch": "Main",                  // "Main" | "MBS #2" | "MBS Dembi Dollo"
  "primary_mobile_number": "+251911223344",
  "national_id_fan": "1234567890123456",  // optional, exactly 16 digits if present
  "nationality": "Ethiopian",
  "address_line_1": "…",
  "kebele": "05",
  "sub_city": "",                    // Main/M2 only; DD leaves blank
  "city": "Dembi Dollo",             // DD fixed; Main uses "Adama"
  "state": "Oromia",
  "country": "Ethiopia",
  "image": "/files/student.jpg",             // from upload_file_guest
  "birth_certificate_image": "/files/bc.jpg",// REQUIRED for Nursery / Nursery AO
  "guardians": [
    {"guardian": "GRD-0001", "guardian_name": "Tesfaye B.", "relation": "Father"}
  ],
  "siblings": []
}
```

`relation` must be one of: `Mother`, `Father`, `Sibling`, `Uncle`, `Aunt`, `Others`.

### 5.2 Student Applicant fields (server-side)

`first_name*`, `middle_name`, `last_name`, `program*` (Link Program),
`academic_year*` (Link), `academic_term`, `student_admission`, `paid` (Check,
default 0), `application_status` (`Applied`/`Approved`/`Rejected`/`Admitted`),
`application_date` (default today), `image`, `birth_certificate_image`,
`date_of_birth`, `gender` (Link), `blood_group`, `student_email_id`,
`custom_school_id`, `student_mobile_number`, `national_id_fin`,
`applicant_type` (`New`/`Existing`, default New), `nationality`,
`address_line_1/2`, `kebele`, `sub_city`, `pincode`, `city`, `state`, `country`,
`guardians` (Table), `siblings` (Table), `student_category`, `title`.

Custom fields added by the app: `branch`, `suggested_student_section`,
`last_application_submitted_on`, `national_id_fan`.

> `national_id_fan` on Student Applicant is marked `unique: 1`. Empty strings
> collide in MariaDB — **always send `null`, never `""`**. Three rows with `""`
> once blocked a whole migration.

### 5.3 `guardian_data` for `create_guardian`

```jsonc
{
  "guardian_name": "Tesfaye Bekele",   // required
  "mobile_number": "911223344",        // required; "+251" prefixed server-side
  "alternate_number": "911223355",
  "email_address": "t@example.com",
  "education": "Bachelor's Degree",    // or "Other" + education_other
  "occupation": "Teacher",             // or "Other" + occupation_other
  "work_address": "…",
  "image": "/files/guardian.jpg"
}
```

Upsert semantics: an existing Guardian with the same `mobile_number` is
**updated**, not duplicated. One guardian legitimately has several children.

### 5.4 `get_existing_student_details` response

```jsonc
{
  "found": true,
  "student": "M1/6134/14",
  "custom_school_id": "M1/6134/14",
  "branch": "Main",
  "first_name": "…", "middle_name": "…", "last_name": "…", "student_name": "…",
  "image": "…", "gender": "Male", "date_of_birth": "2012-03-01",
  "student_mobile_number": "+251…", "student_email_id": "…",
  "national_id_fin": "", "national_id_fan": "", "nationality": "Ethiopian",
  "address_line_1": "", "kebele": "", "sub_city": "", "city": "", "state": "",
  "guardians": [{"guardian": "GRD-1", "guardian_name": "…", "relation": "Father",
                 "mobile_number": "+251…", "education": "…", "occupation": "…"}],
  "current_program": "Grade 6 AO",
  "current_section": "Grade 6 A",
  "is_promoted": true,
  "is_restricted": false,
  "next_program": "Grade 7 AO",
  "suggested_section": "Grade 7 A",
  "can_continue": true,
  "block_reason": ""
}
```

`can_continue` is false **only** when the student is restricted. A student who
was not promoted still re-applies — with the grade pinned to the one they are
repeating (the server ignores a client-sent program in that case).

---

## 6. Business rules — replicate exactly

### 6.1 School ID formats

| Branch | Format | Generator |
|---|---|---|
| Main | `M1/#####/19` | `generate_school_id("M1")` |
| MBS #2 | `M2/#####/19` | `generate_school_id("M2")` |
| Dembi Dollo | `MB/DD/#####/19` | `generate_dd_school_id()` |

`#####` is random 10001–99999, verified unique against **both** Student and
Student Applicant. The trailing `19` is the Ethiopian intake year (2019 E.C.).

**Legacy IDs exist and must not be reformatted**: some students have bare
4-digit IDs (`4167`, `2943`) with no slashes, and there are typos in production
(`Mk1/7656/15`, `M1//8939/17`). Treat the school ID as an opaque string.

**Dembi Dollo has no historical IDs.** On `/apply-dd`, "Existing Student" does
*not* look anything up — it generates a fresh ID exactly like "New Student" and
only tags `applicant_type: "Existing"`.

### 6.2 Student email / login derivation

Canonical form is the school ID with the domain appended **verbatim**:

```
M1/57126/18     ->  M1/57126/18@m.b.s
MB/DD/12935/19  ->  MB/DD/12935/19@m.b.s
4167            ->  4167@m.b.s          (no separators invented)
```

An older convention stripped the slashes (`m15712618@m.b.s`); ~1,300 records
still carry it. **Never generate the slash-less form.** An address outside
`@m.b.s` (a family Gmail) belongs to the parent and must be preserved untouched.

Send `student_email_id: ""` and let the server derive it — it does this on every
write path now.

### 6.3 Branch derivation

Priority order: ID starts `MB/DD` → `MBS Dembi Dollo`; starts `M2/` → `MBS #2`;
else an explicit form choice; else `Main`.

### 6.4 Phone numbers

Ethiopian mobile: 9 digits entered after a fixed `+251` prefix, matching
`^[0-9]{9}$` (users type `911223344`). Store as `+251911223344`.

### 6.5 National ID

- `national_id_fin` — legacy, exactly **12** digits if present
- `national_id_fan` — current, exactly **16** digits if present
- Both optional; send `null` when blank (see §5.2)

### 6.6 Promotion sequence

`Nursery → LKG → UKG → Grade 1 → … → Grade 12`, preserving the medium suffix
(`AO`) where the target program exists. Streams (`NS`/`SS`) begin at Grade 11 and
default to `NS`. Grade 12 returns `None` — graduated, cannot re-apply.

### 6.7 Section suggestion

Existing students carry their section letter forward (`Grade 6 A` → `Grade 7 A`)
when the next program has it. New students are assigned round-robin by fewest
members, tie-broken by fewest of the same gender, then by name. Non-binding — a
human still does the final enrollment.

### 6.8 Ethiopian calendar

The form defaults to **Ethiopian** date entry and converts to Gregorian before
submitting. 13 months; month names are rendered in Afaan Oromo:

```
1 Fulbaana · 2 Onkololeessa · 3 Sadaasa · 4 Muddee · 5 Amajjii · 6 Guraandhala
7 Bitooteessa · 8 Ebla · 9 Caamsaa · 10 Waxabajjii · 11 Adooleessa · 12 Hagayya
13 Qaammee
```

Months 1–12 have 30 days; month 13 has 5 (6 in a leap year). Use a tested
library (`ethiopian-date`, or port the current converter) rather than
approximating with `year - 8`.

### 6.9 Programs (Dembi Dollo)

`Nursery AO`, `LKG AO`, `UKG AO`, `Grade 1 AO` … `Grade 8 AO`.
Main/MBS #2 have a wider list — fetch via `get_programs_for_application`.

**Nursery and Nursery AO require a birth certificate image.**

### 6.10 Fixed values

- DD: `city = "Dembi Dollo"`, `state = "Oromia"`, kebele is free text
- Main: `city = "Adama"`, sub-city + kebele come from `get_kebele_subcity_data`
- `country = "Ethiopia"`, `nationality = "Ethiopian"`
- Current intake: `academic_year = "2019 E.C."`

---

## 7. Error handling — a hard requirement, not a nicety

The single biggest complaint about the current pages: every failure shows
"Failed to submit application. Please try again in a moment." Registrars cannot
report what went wrong, and the real cause sits in a Frappe Error Log nobody
opens.

The rebuild must:

1. **Parse `_server_messages` first** (§3.1). Never show a canned string when the
   server sent a reason.
2. **Show the reason on the page**, in a panel that persists until dismissed —
   not a toast that disappears. Include a **Copy** button.
3. **Show which step failed.** Submission is a multi-call sequence (guardians →
   school ID → applicant). Report *"Step 2 of 3: generate school ID"*, not just
   "failed".
4. **Carry a correlation id.** Generate a UUID per submission, send it as
   `X-Request-Id`, log it in the Worker, and display it. That id ties the
   browser error to the Worker log to the Frappe Error Log.
5. **Log server-side too.** The Worker should record every failed call (endpoint,
   status, correlation id, sanitized payload, user) to D1 or Workers Analytics
   Engine, with a staff-visible page listing recent failures.
6. **Never lose the form.** On failure the entered data stays; add a "Retry" that
   resumes from the failed step rather than recreating guardians.
7. **Surface partial success.** If guardians were created but the applicant
   failed, say so — otherwise a retry silently duplicates work.

Suggested panel content: step, human message, correlation id, HTTP status,
timestamp, and a collapsed raw payload.

---

## 8. PWA and push notifications

- **Manifest**: standalone display, portrait, maskable 192/512 icons, brand
  theme colour.
- **Service worker** (Workbox): app shell precached; API calls network-first.
- **Offline drafts** — high value here, connectivity at registration desks is
  unreliable. Persist the in-progress form to IndexedDB on every step change;
  queue completed submissions via Background Sync and flush when online. Show a
  clear "3 pending submissions" indicator; never silently drop one.
- **Install prompt**: capture `beforeinstallprompt`, offer an Install button.
- **Push**: Web Push (VAPID) through the service worker. Register the
  subscription with the existing `register_device_token` endpoint —
  `device_type: "web"`. Deduplicate tokens (see §4 warning).

Photo capture matters: guardian and student photos are taken on phones. Use
`<input type="file" accept="image/*" capture="environment">` and compress
client-side (~1600px, JPEG ~0.8) before upload — current uploads are unresized
and slow on mobile data.

---

## 9. Known bugs and traps in the current system

### 9.1 The audit-log system can abort registrations (one instance fixed)

A `Student Data Change Log` doctype and nine `SDCL - *` Server Scripts were added
on 2026-08-09 to record every change to student-related doctypes. They are
`After Save` / `After Insert` hooks that insert a log row.

**None of the ten scripts wrap their insert in `try`/`except`.** A log row that
fails to validate therefore raises inside the parent document's `on_update`, and
the entire transaction — the registration — rolls back. An audit log that can
veto the thing it is auditing is worth designing out of the replacement: log
failures should be swallowed and reported, never propagated.

This bit hard once already. `SDCL - Student Diff` emitted three activity types
(`Guardian Added`, `Guardian Removed`, `Reversal Recorded`) that were missing
from the `activity_type` Select, so **every existing-student submission failed**
— 33 logged occurrences, and the reason never reached the user because of the
swallowing described in §7:

```
File "education/api.py", line 3654, in submit_existing_student_application
    student.save(ignore_permissions=True)
  → runs Server Script "SDCL - Student Diff" (DocType Event: Student, After Save)
  → inserts a "Student Data Change Log" row with activity_type = "Guardian Added"
ValidationError: Activity Type cannot be "Guardian Added".
```

`Student Data Change Log.activity_type` is a Select, and those three values were
not among its options.

**Resolved 2026-08-10** by adding `Guardian Added`, `Guardian Removed` and
`Reversal Recorded` to the Select (now 32 options). Registration writes Students,
which fires these hooks, so the new app is exposed to exactly the same class of
failure: whenever an `SDCL` script gains a new activity type, add the option at
the same time, or a whole registration path dies with a message the user never
sees.

The related `Restriction Hooks` script (Student / Before Save) was investigated
and is **not** implicated — it contains no `frappe.throw` or `raise`, and is a
no-op unless `restricted` is set.

Allowed values (after the fix): `Restriction Applied`, `Restriction Cleared`,
`Restriction Reason Changed`, `Student Enabled`, `Student Disabled`,
`Date of Leaving Set`, `Reason for Leaving Changed`, `Name Changed`,
`School ID Changed`, `Student Category Changed`, `Joining Date Changed`,
`Suspension Date Changed`, `Email Changed`, `Transport Mode Changed`,
`Student Added to Group`, `Student Removed from Group`,
`Student Group Active Changed`, `Student Group Dissolved`, `Program Enrolled`,
`Program Enrollment Updated`, `Program Unenrolled`, `Discipline Incident Filed`,
`Discipline Incident Resolved`, `Leave Application Submitted`,
`Leave Application Approved`, `Leave Application Rejected`, `Applicant Approved`,
`Student Deleted`, `Manual Entry`, `Guardian Added`, `Guardian Removed`,
`Reversal Recorded`.

### 9.2 The Desk override trap

`Student Application Page Settings` can serve a database copy of a page instead
of the deployed file. `/mbreg1825` has had this on for some time, serving HTML
that still contains the **old** existing-student flow — so recent deploys never
reached it. Once the app moves off Frappe this stops mattering, but until
cutover, remember any fix to `/mbreg1825` is invisible while that override is on.

### 9.3 Jinja vs Vue `{{ }}`

Frappe renders these pages through Jinja, which uses the same delimiters as Vue.
The current code works around it with `v-text` everywhere. **In a standalone app
this problem disappears entirely** — use normal templating.

### 9.4 Other production data facts

- Both `Student.student_email_id` and `Student.custom_school_id` are `unique: 1`.
- `Student` is named by `custom_school_id`; `Student Applicant` uses `SA-{#####}`
  in the doctype but production rows carry random 10-char names.
- Saving a Student triggers automatic Frappe **User** creation from
  `student_email_id`, and re-points `Student.user` to the account matching the
  current address. Sending a wrong address silently reassigns a login.
- A handful of students share a guardian; never dedupe applicants by phone.

---

## 10. Build order

1. **Worker skeleton + auth.** Session login, role enforcement, one proxied
   endpoint (`get_dd_applied_students`) end to end. Prove no secret is client-side.
2. **Error plumbing (§7) before any form work.** Correlation ids, `_server_messages`
   parsing, the persistent panel, Worker-side logging. Everything after this is
   far easier to debug.
3. **Read-only views.** Applicant list with search, type, paid status, detail.
   Low risk, immediately useful, exercises the whole stack.
4. **New-student form**, Dembi Dollo first (simplest: fixed city, free-text
   kebele, 11 programs).
5. **Existing-student flow** (Main/M2 lookup + promotion) — after §9.1 is fixed.
6. **PWA**: manifest, service worker, offline drafts, background sync.
7. **Push notifications.**
8. **Main + MBS #2 form** (sub-city/kebele reference data, wider program list).
9. **Cutover**: redirect the Frappe routes to the new app.

## 11. Acceptance checklist

- [ ] No Frappe key or secret appears in any browser bundle or network response
- [ ] Every failure shows step, reason, and correlation id — no canned messages
- [ ] Submitting mid-flight offline queues and later flushes exactly once
- [ ] New DD student produces `MB/DD/#####/19` and `MB/DD/#####/19@m.b.s`
- [ ] A 4-digit legacy ID is never rewritten or given separators
- [ ] `national_id_fan` sends `null`, never `""`
- [ ] Nursery/Nursery AO blocks submission without a birth certificate
- [ ] Ethiopian → Gregorian conversion matches the current form across all 13 months
- [ ] Existing student who was not promoted repeats their grade, not the next one
- [ ] Restricted student is refused with the reason shown
- [ ] One guardian registering three children creates one Guardian, three applicants
- [ ] A staff member without `DD Student Registrar` cannot reach DD endpoints
- [ ] Installs as a PWA and receives a test push

---

## 12. Environment

```
FRAPPE_BASE_URL      = https://app.makkobillischool.com
FRAPPE_API_KEY       = <worker secret>
FRAPPE_API_SECRET    = <worker secret>
SESSION_JWT_SECRET   = <worker secret>
VAPID_PUBLIC_KEY     = <worker secret>
VAPID_PRIVATE_KEY    = <worker secret>
```

Create the service account in Frappe under **User → API Access → Generate Keys**.
Give it the narrowest role set that still works: `DD Student Registrar` plus
whichever of `Academics User` / `Education Manager` the read-only views need.
Do not use an Administrator key.

**Test against a staging site first.** These endpoints create Students,
Guardians and Users; a bad loop against production creates real records and real
logins.
