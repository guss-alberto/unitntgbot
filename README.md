# unitntgbot

Telegram Bot for the University of Trento

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

  - University taxes to pay (with "already payed" option)
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
