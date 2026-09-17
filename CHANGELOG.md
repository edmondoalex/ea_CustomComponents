# Changelog

## [Unreleased]

## [1.4.1] - 2026-09-17
- Aggiunto il sensore `Ultimo Evento Numero Camera` con il canale dell'ultima Rule valida con azione `Start`.

## [1.4.0] - 2026-09-17
- Aggiunta la camera `Ultima Regola`, aggiornata esclusivamente da regole valide con azione `Start`.
- Ripristinata la camera `Ultimo Evento` per tutti gli eventi Dahua, separandola dalla nuova entita filtrata.

## [1.3.4] - 2026-09-17
- Spostati icona e logo nella cartella `brand/` richiesta da Home Assistant per la visualizzazione nell'interfaccia.

## [1.3.3] - 2026-09-17
- Mostrata chiaramente nel README HACS la versione del componente installato.

## [1.3.2] - 2026-09-17
- Aggiunto il logo del progetto al pacchetto del componente.

## [1.3.1] - 2026-09-17
- La camera dinamica `Ultimo Evento` conserva lo snapshot acquisito all'arrivo di una regola valida con azione `Start`.
- Aggiunto l'evento Home Assistant `dahua_event_listener_rule_snapshot` con regola, canale, codice, azione e data di acquisizione.
- Aggiunti alla camera dinamica gli attributi dell'ultima regola fotografata.

## [1.3.0]
- Migliorata robustezza stream: watchdog su eventi non utili, backoff con jitter e gestione errori di riconnessione.
