# Changelog

## [Unreleased]

## [1.5.1] - 2026-09-18
- Corretto il salvataggio dell'opzione RTSP subtype: i valori `0` e `1` sono ora selezioni testuali obbligatorie e persistenti.

## [1.5.0] - 2026-09-18
- Aggiunto streaming RTSP alle camere statiche.
- Aggiunta generazione selettiva delle immagini da RTSP per i canali configurati, senza modificare gli snapshot HTTP degli altri canali.
- Aggiunte opzioni per porta RTSP, main/substream e lista canali RTSP.
- Le credenziali RTSP vengono lette dalla configurazione e codificate correttamente nell'URL.

## [1.4.7] - 2026-09-18
- Ripristinata l'implementazione snapshot stabile dopo la regressione introdotta nella versione 1.4.6.

## [1.4.5] - 2026-09-17
- Aggiunta una roadmap pubblica per la possibile integrazione futura di RTSP e registrazioni NVR.
- Collegato `Constantini21/intelbras_dvr` come progetto tecnico di riferimento, senza introdurre dipendenze o funzionalità non ancora implementate.

## [1.4.4] - 2026-09-17
- Aggiunto il sensore `Ultimo Evento Regola Name`, che conserva il nome dell'ultima Rule valida con azione `Start`.
- Aggiunto il sensore `Ultimo Evento Rule Nome Camera`, associando i nomi ricevuti dagli eventi `VideoMotion` al canale dell'ultima Rule.

## [1.4.3] - 2026-09-17
- Corretto il filtro Rule: foto e numero camera richiedono ora `RuleId`/`RuleID`, evitando che eventi `VideoMotion` con campo `Name` sovrascrivano l'ultima Rule reale.

## [1.4.2] - 2026-09-17
- Nuova release HACS versionata, successiva alla precedente installazione basata sul commit Git.

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
