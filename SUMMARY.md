# Project summary · Front Door for events

Status on 7 November 2026. Based on the repository files and its 18 commits (4 to 7 November). Anything unclear is marked as **to be confirmed**.

**Checks run when writing this summary:**

| Check | Result |
|---|---|
| `python3 scripts/validar_datos.py` | All correct: 6 venues, 25 media items (24 approved), 10 inventory items |
| `python3 scripts/test_recomendar.py` | **21/21** cases correct |
| `python3 scripts/test_puntuar_lead.py` | **10/10** cases correct |
| `borradores/` | Does not exist: no drafts pending |

---

## 1. What we are building and for whom

A "front door" chatbot for a company that rents event venues in Barcelona (name still pending: `[EMPRESA]`). It talks to visitors on the website, understands what they want, and either solves it or passes it to the right person. It is the prototype for our master's at La Salle (course *AI in Business*), and it will be presented in one slide for senior management. Synthetic data only. *(Sources: `AGENTS.md`, `KNOWLEDGE.md` §1–2)*

How we work: the team writes the content (skills, data, texts) and Claude Code runs it, tests it and saves it. Each commit is made when the team approves it. *(`AGENTS.md`, `KNOWLEDGE.md` §3)*

---

## 2. Status at a glance

| Piece | Status | Where |
|---|---|---|
| Team context | Done | `AGENTS.md` (27 lines, 5 rules), `CLAUDE.md` (`@AGENTS.md`), `KNOWLEDGE.md` |
| Data: catalogue and inventory | Done | `data/espacios.json` (6 venues), `data/inventario.json` (10 extras) |
| Data validator | Done | `scripts/validar_datos.py` |
| Skill 8 · guardrails | Done | `.claude/skills/guardrails/` |
| Skill 7 · consentimiento | Done | `.claude/skills/consentimiento/` |
| Skill 2 · recomendador-espacios | Done | `.claude/skills/recomendador-espacios/` + `scripts/recomendar.py` |
| Skill 4 · cualificador-leads | Done | `.claude/skills/cualificador-leads/` + `scripts/puntuar_lead.py` |
| Skill 3 · media-espacios | Done | `.claude/skills/media-espacios/` (uses `recomendar.py`) |
| Skill 1 · router-intenciones | Pending | Does not exist yet |
| Skill 5 · disponibilidad-inventario | Pending | Depends on n8n (`KNOWLEDGE.md` §2) |
| Skill 6 · gestor-reservas | Pending | Depends on n8n. Part of the pre-booking is already covered by the qualifier (the hold offer and the message after the "sí" (yes)); the final split between the two skills is **to be confirmed** |
| Plugin `eventos-front-door` | Pending | No `plugins/` folder (plan in `KNOWLEDGE.md` §4 and §7) |
| Web chat | Pending | Plan: rule-based, local, no external API (`KNOWLEDGE.md` §3) |
| n8n (webhook, Google Sheets) | Pending | Until then, everything from n8n is marked SIMULADO |
| Real media (photos, floor plans, tour) | Pending | Everything is a placeholder for now (`illustrative: true`, paths `/media/placeholders/`) |
| Metrics dashboard | Pending | `KNOWLEDGE.md` §7, step 10 |
| Executive slide | Pending | `KNOWLEDGE.md` §7, step 12 |
| GitHub for the group | Pending | Nobody has an account yet (`KNOWLEDGE.md` §3) |

---

## 3. Key team decisions

| Topic | Decision | Why |
|---|---|---|
| Tool | Claude Code builds and runs; the team writes the content | The professor allowed it; the first trial was with Codex (`KNOWLEDGE.md` §3–4, commit `3585c67`) |
| Prices | The chatbot never gives prices or quotes; it does ask for the client's budget | The price depends on date, set-up and services: the sales rep prepares it (`AGENTS.md` rule 2) |
| Availability | Never confirmed without real data from n8n; simulated data is marked SIMULADO and never shown as confirmed | Avoid false promises in the demo (`AGENTS.md`, guardrails rule 2) |
| Discounts | Never granted or hinted at; passed to the sales rep | A person decides (`AGENTS.md` rule 5) |
| Decide with rules | Recommendation, scoring and escalations are decided by a script or a fixed table; the LLM only writes the text | In the trial, the LLM scored the same data 60, 20 and 40 (`KNOWLEDGE.md` §3 and §5) |
| 90 % rule | Above 90 % of the capacity for the requested layout → "al límite" (at the limit): recommended later, with a warning | Don't fill a venue to the last seat without warning (`KNOWLEDGE.md` §3.1) |
| 60 % rule | Below 60 % it is not recommended, unless there is no other option. If the only option is at the limit, the first venue below 60 % is added as an alternative | A half-empty venue looks bad; but the client should have an alternative (`KNOWLEDGE.md` §3.1; recommender skill §2) |
| Pre-booking | Free provisional hold for 72 working hours, only with more than 70 points, an exact day, a chosen venue and enough lead time, and with an explicit "sí" (yes) | Dates are only held for serious, concrete leads; the final booking is confirmed by the sales rep (`KNOWLEDGE.md` §3.1; qualifier skill §4) |
| Qualifier weights | Date 25 · attendees 20 · budget 20 · type 15 · company 10 · urgency 10, with fixed levels and a phrase → level table | Same weights as in the trial, decided on 7/11; the table stops the LLM from choosing the level (`KNOWLEDGE.md` §5; qualifier skill §2–3) |
| Escalations | 6 `decision` values, each with who receives it and the deadline; 14 escalation reasons (plus `—`) | Nobody is left without an answer, and everything can be measured (`KNOWLEDGE.md` §3.1 and contract) |
| Support hours | Monday to Saturday, 9–18 h. "24 h laborables" (24 working hours) = at most, the next working day at the same time. If they ask for a person: under 2 h during opening hours | Deadlines the client can understand (`KNOWLEDGE.md` §3.1) |
| Consent | AI notice in the first message; contact details only when needed; explicit permission before saving; marketing asked separately, once; withdrawing permission takes effect immediately | GDPR and data minimisation (consentimiento skill) |
| Consent log | `registros/consentimientos.jsonl` (with n8n, a tab in the Sheet), explicit answers only | To be able to prove each permission (`KNOWLEDGE.md` §3) |
| Media | Approved material only; card photo chosen by layout; never from an area that closes earlier; never the file path; "Imagen ilustrativa" (Illustrative image) if `illustrative: true` | Never show anything that does not exist or is not approved (media skill) |
| Team contact | atencion@empresa-eventos.example · +34 930 000 000 (synthetic) | Needed to close offensive conversations and for clients who give no contact (correction 02, round 4) |

---

## 4. Skills

All tests were done by Claude Code answering **as if it were the chatbot**, applying the skills and running the scripts. There is no web chat yet that does this on its own (see §8).

### Guardrails (`.claude/skills/guardrails/SKILL.md`)
- **What it does:** checks every reply before it is sent (prices, availability, discounts, internal and sensitive data, capacity, venue policies, topic, language) and decides whether to pass to a person.
- **Rounds:** 3 tests and 4 correction rounds.
  - Test 01: 12 phrases; 7 pass and 5 partly.
  - Test 02: 18 phrases; 14 pass and 4 partly.
  - Test 03: 10 turns; 9 pass. After round 4, all 11 turns in the repeat pass.
- **What failed and how it was fixed:**
  - "Lo compruebo" (I'll check) replies had no `decision`, no who and no when → decision table with owners and deadlines.
  - The Jardí example hinted that the party could run later → new "Mal" (Bad) example.
  - There was no reason for frustration → `frustracion`.
  - It was unclear whether the first insult was escalated → first insult: warning, and the chat continues.
  - The team contact and the meaning of "24 h laborables" (24 working hours) were missing → synthetic contact and a definition of "24 h laborables".
  - The availability message talked about "bloquear" (holding the date) when there were no holds yet → new message (commit `6a11b2c`).
- **Files:** `pruebas/prueba-guardrails-01.md`, `-02.md`, `-03.md` · `pruebas/correccion-02-guardrails.md` · commits `e323834`, `6a11b2c`, `1d8b780`.

### Consentimiento (`.claude/skills/consentimiento/SKILL.md`)
- **What it does:** AI notice, when and which personal data are asked for, permission before saving, marketing asked separately, a log entry for each permission, and how to withdraw permission or delete data.
- **Rounds:** 2 tests.
  - Test 01: 9 conversations; 5 pass and 4 partly.
  - Test 02: 6 repeated cases; all 6 pass.
- **What failed and how it was fixed:**
  - Pre-booking was impossible without weights → passed to the sales rep with reason `lead`.
  - It asked permission for an email that was not needed → it now separates asking for it ourselves from the client giving it.
  - No other contact was offered if the client refused one → the alternative is offered once.
  - Withdrawing permission was sent to the team → it now takes effect immediately.
  - There was no state for deletion → `borrado_solicitado`, with its own purpose.
  - It was not decided where the log is stored → a second contract in `KNOWLEDGE.md`.
- **Files:** `pruebas/prueba-consentimiento-01.md`, `-02.md` · `pruebas/correccion-03-consentimiento.md` · commits `bea7691`, `6a11b2c`.

### Venue recommender (`.claude/skills/recomendador-espacios/SKILL.md`)
- **What it does:** recommends 1 to 3 venues in cards without prices. The choice and the order are decided by `scripts/recomendar.py`.
- **Rounds:** 3 tests.
  - Test 01: 4 phrases.
  - Test 02: 6 phrases.
  - Test 03: 4 phrases.
  - All passed, but each round left open points that the team closed.
- **What failed and how it was fixed:**
  - The Jardí was treated differently in guardrails and in the recommender → its own message for the Jardí.
  - There was no warning about the Mirador terrace → `zone_end_times` and `avisos_zona` in the script.
  - There was no message for when the only option is at the limit → an "única opción" (only option) message and an alternative below 60 %.
  - A tie depended on the order of the JSON → tie-break by smaller capacity, compared with exact fractions.
  - The LLM made up the "por qué encaja" (why it fits) line → `event_types` per venue.
  - Times were ambiguous → rule for 1 to 7 (early morning) and 8 to 12 (the chatbot asks).
  - Occupancy could appear in the reply → it is internal data.
  - Claude Code's mistake in test 03: it forgot the terrace hours when writing the reply → the script now gives the warning.
- **Files:** `pruebas/prueba-recomendador-01.md`, `-02.md`, `-03.md` · `pruebas/correccion-04-recomendador.md` · commits `591885a`, `edbbc78`, `72eadfe`, `5596168`.

### Lead qualifier (`.claude/skills/cualificador-leads/SKILL.md`)
- **What it does:** collects date, attendees, budget, type, company and urgency, scores 0 to 100 with `scripts/puntuar_lead.py`, and decides between the provisional hold and passing to the sales rep.
- **Rounds:** 2 tests.
  - Test 01: dinner for 120 and wedding; both pass.
  - Test 02: the dinner repeated; passes.
- **What failed and how it was fixed:**
  - There was no message after the "sí" (yes) to the hold, with the risk of showing something SIMULADO as confirmed → fixed messages for simulated and for real.
  - "Unos" (about) scored differently for attendees and budget → always approximate.
  - It did not say what to do if both the day and the venue were missing → both are asked.
  - The type was always checked against the first venue → reference venue: the chosen one, otherwise the first.
  - The LLM decided how to turn phrases into levels → fixed table, and "este mes" (this month) calculated with the real date.
  - Two different deadlines in two messages in a row → deadlines unified (commit `2e175ae`).
- **Files:** `pruebas/prueba-cualificador-01.md`, `-02.md` · `pruebas/correccion-05-cualificador.md` · commits `7968a5d`, `2e175ae`.

### Venue media (`.claude/skills/media-espacios/SKILL.md`)
- **What it does:** chooses the photo for each card and shows approved photos, floor plan or 360° tour, without paths. It says when something does not exist (there are no videos).
- **Rounds:** 2 tests.
  - Test 01: 5 phrases; all 5 pass.
  - Test 02: 6 phrases; all 6 pass.
- **What failed and how it was fixed:**
  - "Imagen ilustrativa" (Illustrative image) had no data behind it → `illustrative` on all 25 items.
  - The photo of the closed terrace appeared, or appeared for a conference → `zone` and an indoor-before-outdoor rule.
  - The LLM looked up media in the data → `media_aprobada` function in the script.
  - The Mirador had no theatre photo → `mirador-montjuic-foto-03` (commit `7387f50`).
- **Files:** `pruebas/prueba-media-01.md`, `-02.md` · `pruebas/correccion-06-media.md` · commits `434d83a`, `7387f50`.

### Data (not a skill, but it had its own correction)
- **Review:** 9 inconsistencies were found in the data. The team decided each one; for example, the cloakroom can no longer be used in the Atelier, and the Mirador tagline was aligned with its `full_profile`. `pruebas/correccion-01-datos.md` · commits `7a5ebe4`, `121a83b`.

---

## 5. Scripts and tests

| Script | What it decides | Tests |
|---|---|---|
| `scripts/validar_datos.py` | That the data follow the team's rules: 6 venues with all fields; capacities in order (cocktail > theater > banquet > classroom) and `absolute_max` equal to the largest; no old fields and no word "ficticio/a"; `max_end_time` and `zone_end_times` in HH:MM format; `event_types`; media with a valid type, `approved`, `illustrative`, `disposition` on approved photos, and at least one approved photo and floor plan per venue; inventory with stock > 0 and existing venues | All correct with the real data. In each round it was tested on a copy with deliberate errors, and it caught all of them |
| `scripts/recomendar.py` | Which venues are recommended and in what order: capacity for the layout, lead time, end time, groups `comodo` / `al_limite` / `bajo_60`, order by closeness to 80 % with a tie-break, alternative, maximum 3, discarded venues with the reason, area warnings and card photo. Also approved media by type (`--media`) | **21/21** (`scripts/test_recomendar.py`): the 8 cases calculated by the team, tie-break, alternative, area warning, 6 photo cases and 4 media cases |
| `scripts/puntuar_lead.py` | The lead score (0–100) with the skill's levels; type based on the reference venue; "este mes" (this month) with the real date; the decision (`prerreserva` only if all 4 conditions are met) and which conditions are missing | **10/10** (`scripts/test_puntuar_lead.py`): the team's 5 cases (80, 90, 30, 85, 70), the 4 new cases requested and 1 case on the priority of the chosen venue |

---

## 6. Evidence for class (lab sheet)

| Evidence (`KNOWLEDGE.md` §1) | Status | File or commit |
|---|---|---|
| 1. Team context saved | Done | `AGENTS.md` (`4b17310`), `CLAUDE.md` (`5f00b31`), `KNOWLEDGE.md` |
| 2. A useful skill, created or found | Done (5 skills created by the team) | For example, guardrails (`e323834`) or the qualifier (`7968a5d`) |
| 3. Skill packaged as a plugin | **Pending** | No `plugins/` yet. Plan in `KNOWLEDGE.md` §4 |
| 4. Task tested with a recorded correction | Done (6 corrections) | For example, `pruebas/prueba-guardrails-01.md` → `pruebas/correccion-02-guardrails.md` |
| 5. Known limitation and what is still pending | Done | Comments in each test, "Pendiente" (Pending) in `KNOWLEDGE.md` §3.1 and section 8 of this summary |

---

## 7. Course concepts applied

| Concept | Concrete example from the project |
|---|---|
| LLMs vs. decision models | The score is calculated by `puntuar_lead.py` with fixed weights, because in the trial the LLM scored the same data 60, 20 and 40. The recommendation is decided by `recomendar.py`; the LLM only writes the cards |
| Human-in-the-loop | Discounts, complaints, exceptions and permits always go to a person. The hold needs an explicit "sí" (yes), and only the sales rep confirms the final booking. In daily work, the team writes each skill and approves each commit |
| Where AI gets it wrong | The tests showed it several times. A skill example hinted that a party could run later. The LLM had to "stretch" the reason for a recommendation. In prueba-recomendador-03, Claude Code forgot the terrace hours. With decimals, a tie did not come out as a tie. Each case ended up as a rule or in a script |
| Challenge the headline | "Passing the validator does not mean the data make sense": the data passed it and still had 9 inconsistencies (correction 01). The tests count partial passes, not only successes (for example, 7 of 12 in guardrails 01). The metrics for the slide are **pending** |
| AI workflows | Skills that work together (guardrails + consentimiento + recommender + qualifier + media), scripts as tools, and n8n as the background process. n8n is still simulated |
| Acceleration vs. automation | The chatbot only handles the simple parts on its own: information, recommendation and qualification. The hold is provisional, and the price and the final booking stay with the sales rep |
| Lead journey | The demo's main route: enquiry → qualification → recommendation → provisional hold → sales rep's proposal (tested in `pruebas/prueba-cualificador-02.md`) |
| Capacity and total cost | **Pending**: it goes in the slide (`KNOWLEDGE.md` §2) |

---

## 8. Pending work and known limitations

**Still to build**
- Skills 1 (router-intenciones), 5 (disponibilidad-inventario) and 6 (gestor-reservas).
- Plugin `eventos-front-door`, web chat, n8n, dashboard, slide and GitHub.
- Company name (and the `project` field in `espacios.json`, which is still in English).
- Real media: AI-generated photos, SVG floor plans and a page for the 360° tour.

**Pending for the web chat and n8n** (`KNOWLEDGE.md` §3.1)
- Always mask cards, IBAN and ID numbers, and email and phone if there is no permission, before saving or sending to n8n.
- Use the real date and time: support hours, "este mes" (this month) and lead time.
- If the client withdraws permission, also delete their data from the Sheet.
- Create `registros/consentimientos.jsonl`: it does not exist yet, because there is no chat to write to it.

**Known limitations**
- **The tests are simulated:** Claude Code answers as the chatbot. It has not been tested with a real chat or a real client yet.
- **Everything that depends on n8n is SIMULADO:** availability, holds and stock.
- **The LLM still turns phrases into levels** (qualifier) and writes the replies. The fixed table limits this, but does not remove it.
- **The inventory of extras** (`data/inventario.json`) is only checked by the validator: no skill and no decision script uses it yet.
- **To be confirmed:** whether `/plugin` works in the desktop app or needs the terminal, and whether a new session is needed after installing (`KNOWLEDGE.md` §4).
- **To be confirmed:** the **buying-committee-simulator** skill appears in `KNOWLEDGE.md` §2 as "ya probada" (already tested), but it is not in this repository. It comes from the earlier trial (`reservas-eventos`).
- **`KNOWLEDGE.md` §7 ("Estado actual", current status) is out of date:** it still says step 4 (guardrails and consentimiento) is pending, and the "Última actualización" (last updated) date is 5 November.
