# Roadmap di Dahua Event Listener

Questo documento raccoglie idee e riferimenti per evoluzioni future. Le funzioni elencate non sono ancora disponibili e saranno implementate solo dopo verifiche tecniche e test su dispositivi Dahua reali.

## Area video e registrazioni

Il progetto [Constantini21/intelbras_dvr](https://github.com/Constantini21/intelbras_dvr) è mantenuto come riferimento tecnico per alcune capacità complementari al listener eventi:

- snapshot HTTP con autenticazione Digest;
- streaming RTSP live per canale;
- selezione main stream/substream;
- consultazione delle registrazioni tramite Media Browser;
- navigazione per canale, data, ora e segmento;
- conversione del playback RTSP in HLS tramite Home Assistant;
- aggiornamento di host e credenziali;
- tracciamento opzionale dell'indirizzo IP tramite MAC.

Il collegamento è puramente informativo: `intelbras_dvr` non è una dipendenza di Dahua Event Listener e non viene installato automaticamente.

## Funzioni candidate

### 1. Streaming RTSP

Valutare l'estensione delle camere statiche esistenti con live view RTSP e scelta configurabile tra flusso principale e secondario.

### 2. Registrazioni nel Media Browser

Valutare un provider Media Source che permetta di navigare le registrazioni dell'NVR per canale, giorno, ora e intervallo.

### 3. Rule collegata alla registrazione

Usare i dati già disponibili (`channel`, `rule_id`, nome regola e orario) per aprire direttamente il tratto registrato relativo a un evento AI.

### 4. Gestione delle sessioni

Prevedere limiti e timeout configurabili per non saturare il numero ridotto di sessioni RTSP simultanee supportate da alcuni NVR.

### 5. Compatibilità e configurazione

Conservare gli unique ID esistenti e mantenere separati:

- il listener push `eventManager.cgi`;
- le fotografie congelate delle Rule;
- lo streaming live;
- il playback delle registrazioni.

## Criteri prima dell'implementazione

- Verificare API e URL su NVR Dahua reali, non soltanto Intelbras.
- Controllare licenza e attribuzione prima di riutilizzare eventuale codice.
- Misurare l'impatto di RTSP/HLS su Home Assistant e sull'NVR.
- Testare autenticazione, riconnessione e disponibilità delle registrazioni.
- Introdurre le funzioni in modo opzionale e retrocompatibile.

## Tracciamento

La discussione tecnica è disponibile nella [issue Roadmap: streaming RTSP e registrazioni DVR](https://github.com/edmondoalex/ea_CustomComponents/issues/1).
