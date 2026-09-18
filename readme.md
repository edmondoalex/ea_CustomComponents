# Dahua Event Listener

**Versione componente: 1.5.1**

![Logo](logo.png)

Integrazione Home Assistant per ricevere eventi dai dispositivi Dahua (NVR/DVR/camere) tramite `eventManager.cgi` e creare sensori e camere snapshot.

[![Roadmap: RTSP e registrazioni](https://img.shields.io/badge/roadmap-RTSP%20e%20registrazioni-5319e7)](https://github.com/edmondoalex/ea_CustomComponents/issues/1)

> **Sviluppo futuro:** è in valutazione l'integrazione di streaming RTSP, Media Browser e riproduzione delle registrazioni NVR. Il progetto [Constantini21/intelbras_dvr](https://github.com/Constantini21/intelbras_dvr) è stato registrato come riferimento tecnico. Consulta la [roadmap completa](ROADMAP.md) e la [issue di progetto](https://github.com/edmondoalex/ea_CustomComponents/issues/1). Queste funzioni non sono ancora incluse.

## Funzionamento
- L'integrazione apre uno stream HTTP verso il dispositivo Dahua: `eventManager.cgi?action=attach&codes=[All]&heartbeat=5`.
- Ogni evento ricevuto viene parsato e salvato nel coordinator.
- I sensori leggono gli ultimi dati evento.
- Le camere forniscono snapshot: una camera dinamica sull'ultimo canale evento e una camera statica per ogni canale.
- La camera dinamica `Ultimo Evento` segue l'ultimo evento Dahua ricevuto.
- La camera separata `Ultima Regola` conserva esclusivamente la foto di una regola Dahua con `RuleId` e azione `Start`, ignorando `VideoMotion` e gli altri eventi con un semplice campo `Name`.
- Dopo la cattura viene emesso l'evento Home Assistant `dahua_event_listener_rule_snapshot`.
- Lo stream ha reconnect automatico e watchdog in caso di silenzio prolungato.

## Installazione (HACS)
1. HACS -> Integrazioni -> Aggiungi repository personalizzato.
2. Inserisci l'URL della repo GitHub.
3. Installa l'integrazione.
4. Riavvia Home Assistant.

## Configurazione
1. Impostazioni -> Dispositivi e Servizi -> Aggiungi integrazione.
2. Cerca `Dahua Event Listener`.
3. Inserisci:
   - Nome
   - Host (IP o hostname del dispositivo)
   - Username
   - Password
   - Numero canali

## Opzioni
Impostazioni -> Dispositivi e Servizi -> Dahua Event Listener -> Opzioni

Puoi modificare:
- `host`
- `username`
- `password`
- `channels`
- `connect_timeout`
- `read_timeout`
- `idle_reconnect_seconds`
- `reconnect_delay`
- `rtsp_port` (porta RTSP, normalmente `554`)
- `rtsp_subtype` (`0` main stream, `1` substream)
- `rtsp_snapshot_channels` (canali separati da virgola che devono usare RTSP per le immagini, ad esempio `7,14`)

## Entita create
### Sensori
- Event Code
- Event Action
- Index
- Temperature
- Latitudine
- Longitudine
- Action Data
- Direction
- Rule Name
- Object Action
- Object Type
- Raw Data
- Ultimo Evento Numero Camera (canale dell'ultima Rule valida con azione `Start`)
- Ultimo Evento Regola Name (nome dell'ultima Rule valida con azione `Start`)
- Ultimo Evento Rule Nome Camera (nome NVR appreso per il canale dell'ultima Rule valida)

### Camere
- Camera dinamica (ultimo evento)
- Camera dinamica filtrata (ultima regola con azione `Start`)
- Camera statica per ogni canale configurato

## Note importanti
- Le camere statiche espongono anche il live RTSP. I canali elencati in `rtsp_snapshot_channels` usano il flusso RTSP anche per generare l'immagine statica tramite Home Assistant.
- Per applicare modifiche alle opzioni, ricarica l'integrazione o riavvia Home Assistant.

## Roadmap

Le evoluzioni video prese in considerazione comprendono live RTSP, scelta main stream/substream, registrazioni nel Media Browser e collegamento tra Rule e registrazione dello stesso canale/orario. Dettagli, vincoli e fonte di riferimento sono raccolti in [ROADMAP.md](ROADMAP.md).

## Troubleshooting
### L'evento si blocca dopo 1-2 giorni
- Aumenta `read_timeout` o `idle_reconnect_seconds` nelle Opzioni.
- Controlla i log in `Impostazioni -> Sistema -> Log`.

### Errore "Nessun campo data="
- Alcuni dispositivi inviano eventi senza payload JSON; vengono ignorati.

## Log debug
Aggiungi in `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.dahua_event_listener: debug
```

## Versione
Vedi `custom_components/dahua_event_listener/manifest.json`.
