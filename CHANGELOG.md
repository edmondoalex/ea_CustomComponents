# Changelog

## [Unreleased]

## [1.3.1] - 2026-09-17
- La camera dinamica `Ultimo Evento` conserva lo snapshot acquisito all'arrivo di una regola valida con azione `Start`.
- Aggiunto l'evento Home Assistant `dahua_event_listener_rule_snapshot` con regola, canale, codice, azione e data di acquisizione.
- Aggiunti alla camera dinamica gli attributi dell'ultima regola fotografata.

## [1.3.0]
- Migliorata robustezza stream: watchdog su eventi non utili, backoff con jitter e gestione errori di riconnessione.
