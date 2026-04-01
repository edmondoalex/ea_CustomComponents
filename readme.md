# Dahua Event Listener

![Logo](logo.png)

Integrazione Home Assistant per ricevere eventi dai dispositivi Dahua (NVR/DVR/camere) tramite `eventManager.cgi` e creare sensori e camere snapshot.

## Funzionamento
- L'integrazione apre uno stream HTTP verso il dispositivo Dahua: `eventManager.cgi?action=attach&codes=[All]&heartbeat=5`.
- Ogni evento ricevuto viene parsato e salvato nel coordinator.
- I sensori leggono gli ultimi dati evento.
- Le camere forniscono snapshot: una camera dinamica sull'ultimo canale evento e una camera statica per ogni canale.
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

### Camere
- Camera dinamica (ultimo evento)
- Camera statica per ogni canale configurato

## Note importanti
- Le camere sono snapshot, non stream RTSP.
- Per applicare modifiche alle opzioni, ricarica l'integrazione o riavvia Home Assistant.

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
