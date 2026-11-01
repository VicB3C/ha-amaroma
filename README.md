# AMA Roma Raccolta Rifiuti

Integrazione Home Assistant (HACS) che crea un calendario con i giorni di raccolta
rifiuti AMA per il tuo indirizzo a Roma, usando i dati di
[amaroma.it](https://www.amaroma.it/it/servizi/calendario-svuotamento-contenitori).

- Funziona sia con la raccolta porta a porta ("esporre entro le …") sia con i cassonetti stradali (orario di svuotamento).
- Un evento di un giorno intero per ogni raccolta: il titolo è la tipologia (Carta, Organico, …), la descrizione contiene l'orario.
- Ogni 30 giorni (e a ogni riavvio) ricontrolla il sito. Se AMA ha cambiato qualcosa aggiorna il calendario e mostra una notifica.

## Installazione

1. HACS → menu ⋮ → *Repository personalizzati* → URL di questo repository, categoria *Integrazione*.
2. Installa **AMA Roma Raccolta Rifiuti** e riavvia Home Assistant.
3. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → AMA Roma*, inserisci via e civico.

## Esempio di automazione

```yaml
trigger:
  - platform: calendar
    event: start
    entity_id: calendar.raccolta_rifiuti_via_nomentana_44
    offset: "-04:00:00"   # alle 20:00 del giorno prima
action:
  - service: notify.notify
    data:
      message: "Domani: {{ trigger.calendar_event.summary }} – {{ trigger.calendar_event.description }}"
```
