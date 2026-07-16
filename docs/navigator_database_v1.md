# Navigator Vitae Database v1

## Doel

Deze database ondersteunt alle Navigator-modules en bewaart deelnemers, antwoorden, analyses, reviews en finale inzichten.

## Kernentiteiten

- participants
- modules
- questions
- module_runs
- responses
- analyses
- reviews
- final_insights

## Relaties

- één participant heeft meerdere module_runs
- één module heeft meerdere questions
- één module_run heeft meerdere responses
- één module_run kan meerdere analyses hebben
- één analyse kan één of meerdere reviews krijgen
- één module_run resulteert uiteindelijk in één final_insight

## Datastroom

Participant
→ Module
→ Module run
→ Responses
→ Analysis
→ Review
→ Final insight
→ Navigator Operating System


## Entiteit: participants

Doel:
Bewaart de kernidentiteit van elke Navigator-deelnemer.

Velden:

- id
  - type: uuid
  - functie: interne technische sleutel

- navigator_id
  - type: text
  - voorbeeld: NV-2026-000001
  - uniek: ja
  - functie: vaste externe Navigator-identiteit

- first_name
  - type: text

- last_name
  - type: text

- email
  - type: text
  - voorlopig optioneel

- status
  - type: text
  - mogelijke waarden:
    - active
    - paused
    - completed
    - archived

- created_at
  - type: timestamp
  - automatisch ingevuld

- updated_at
  - type: timestamp
  - automatisch bijgewerkt

Ontwerpregels:

- navigator_id verandert nooit
- persoonlijke dossiers worden altijd gekoppeld via de interne uuid
- de gebruiker ziet navigator_id, niet de uuid
- e-mail is niet verplicht in de beta
- verwijderen gebeurt voorlopig niet fysiek; gebruik status = archived