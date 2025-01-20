# unitntgbot

Telegram Bot for the University of Trento

## Fast start

- Per i workspace vedere [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/#workspace-sources) (non ho idea se possano essere utili)
- Per installare le dipendenze `uv sync`
- Per installare pre-commit `pre-commit install` (previa installazione di pre-commit)
- Per eseguire main fare `uv run unitntgbot`

## Functional requirements

- Notifications for lectures (x mins before start)
- locuspocus integration
- expelliarbus integration
- povo maps (?)
- Morning briefing:

  - lectures
  - suggested study rooms
  - menu
  - weather (+)
  - ETA to campus (?)

- broadcasting messages:

  - University taxes to pay (with "already paid" option)
  - Modified lectures time / location / canceled
  - Exam sessions available (?)

## Non functional requirements

- uptime monitoring
- observability (metrics / otel)

## Sources

### Without auth

- lista di lezioni seguite (unitnapp no login)
- modifiche orari lezioni
- easyacademy -> room occupation
- opera4u -> menu mensa
- trentino trasporti -> ritardi bus
- navigazione mappe povo
- scadenza pagamento tasse universitarie
- appelli prenotabili (?)

### With auth

- esami prenotati
- credito mensa
- nuovi voti
