---
name: form-answers
description: Use when answering any application form or portal question: work authorization and sponsorship per status (citizen, permanent resident, F-1 CPT, other), visa type, salary, demographic and voluntary questions, how-did-you-hear, agreements, and questions that must be left to the student.
---
# Form answers

From jev-job-search's answer rules and coop-crew's profile. Every answer comes from `profile/settings.json`,
`profile/facts.md` or the posting. When the profile does not settle a question, leave it for the student and log why.
JEV (the form filler) applies the same rules in code through `vendor/jev/src/data/profile.json`, which
`tools/setup_finish.py` fills from the profile.

## Work authorization (word for word)

The sentence for each country is `work_auth.<country>.sentence`. Use it exactly, with no added or softened words.
For yes/no and dropdown questions:

| Status | Authorized to work in that country now? | Need sponsorship now? | Need sponsorship in the future? |
|---|---|---|---|
| Citizen | Yes | No | No |
| Permanent resident | Yes | No | No |
| F-1 student on CPT (co-op) | Yes, for this co-op through CPT | No (CPT covers it) | As `sponsorship_later` says (usually Yes) |
| Other | As the profile says | As the profile says | As the profile says |

- An F-1 student is currently authorized for a co-op or internship through CPT, so a "currently authorized" question is
  Yes. Future sponsorship follows `sponsorship_later`.
- **Visa type gate.** If `visa_type` is set (for example "F-1 CPT"), a visa-type field gets an option naming it
  (`visa_type_names`). Never choose or write a type in `never_visa_types` (for example H-1B), whatever the options
  offer. If no option names the student's type, leave the field and say so in the field log.
- Never write a work-authorization answer stronger than the profile. When the question is unclear, leave it.

## Standing answers

- **Salary or pay expectations:** "Open, in line with the posted range for this co-op." If a number is forced, use the
  posted range's lower bound only if it is at or above `targets.pay_floor_hourly`; otherwise leave it for the student.
- **Start and end dates:** `coop.start` and `coop.end`; availability text `coop.availability`.
- **Relocation:** only what `profile/locks.md` says.
- **How did you hear about us:** "Company website" for a company board, "NUworks" for NUworks roles. A list of checkboxes
  under this question is a list of sources, never a consent: tick exactly one.
- **Demographic and voluntary self-identification** (gender, race, veteran, disability): "I decline to self-identify" /
  "Prefer not to say", unless the student wrote other answers in their profile.
- **GPA:** only if `program.show_gpa` is true; otherwise leave optional GPA fields blank, and a required one for the
  student.

## Leave for the student (never answer)

- Any field that asks them to type their name to sign or agree to an NDA or a contract, and any NDA.
- Any question that asks the applicant to confirm an answer is their own work written without AI. Do not draft it; put
  it in `out/<id>/soft-flags.md` and the field log as "left for the student: asks for work written without AI".
- Background-check or criminal-history questions.
- Anything the profile does not settle. Log every blank with its reason.
