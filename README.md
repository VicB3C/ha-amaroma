# 🗑️ AMA Roma Raccolta Rifiuti

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.11%2B-18BCF2.svg)](https://www.home-assistant.io)
**Non dimenticare più di portare giù la spazzatura.**
Scrivi la tua via e il civico: Home Assistant crea un calendario con tutti i giorni di raccolta AMA del tuo indirizzo a Roma, e lo tiene aggiornato da solo.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=woody4165&repository=ha-amaroma&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Apri in HACS">
  </a>
</p>

---

## ✨ Cosa fa

| | |
|---|---|
| 📅 **Calendario automatico** | Un evento per ogni raccolta: *Carta*, *Organico*, *Plastica e metalli*, *Indifferenziato* |
| ⏰ **All'orario giusto** | Porta a porta: l'evento inizia all'ora entro cui esporre (es. 20:00–22:00). Cassonetti in strada: all'inizio dello svuotamento. Ogni evento dura 2 ore |
| 🔄 **Sempre aggiornato** | Ogni 30 giorni (e a ogni riavvio) ricontrolla il sito AMA |
| 🔔 **Ti avvisa dei cambi** | Se AMA modifica giorni o orari, il calendario si aggiorna e compare una notifica in Home Assistant. Per riceverla anche sul telefono serve [un'automazione](#-notifica-sul-telefono-quando-ama-cambia-giorni-o-orari) |
| 🔒 **Niente account** | Nessuna registrazione, nessuna chiave: usa gli stessi dati pubblici di [amaroma.it](https://www.amaroma.it/it/servizi/calendario-svuotamento-contenitori) |

## 📦 Installazione

1. Clicca il pulsante **Apri in HACS** qui sopra, oppure in HACS apri **⋮ → Repository personalizzati**, incolla `https://github.com/woody4165/ha-amaroma` e scegli **Integrazione**.
2. Scarica **AMA Roma Raccolta Rifiuti** e **riavvia Home Assistant**.
3. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e cerca **AMA Roma**.
4. Scrivi la **via** (es. `via nomentana`) e il **numero civico**. Fatto!

> Puoi aggiungere l'integrazione più volte per seguire più indirizzi, per esempio casa e ufficio.

## 📅 Il calendario

Trovi il calendario nella pagina **Calendario** di Home Assistant e come entità, per esempio `calendar.raccolta_rifiuti_via_nomentana_44`.
Puoi cambiargli nome e ID da **Impostazioni → Entità → ⚙️**.

**Cosa significa lo stato `on` / `off`?**
Come ogni calendario di Home Assistant, lo stato è:

- **`on`** una raccolta è in corso: per 2 ore dall'ora entro cui esporre;
- **`off`** in questo momento non c'è nessuna raccolta.

Gli attributi dell'entità mostrano la raccolta in corso o la **prossima**: `message` (il tipo di rifiuto), `description` (gli orari), `start_time`, `end_time`.

## 🔔 Esempio: avviso la sera prima

Ogni sera alle 20:00 ti dice cosa esporre il giorno dopo (e niente, se non c'è raccolta):

```yaml
alias: Promemoria spazzatura
triggers:
  - trigger: time
    at: "20:00:00"
actions:
  - action: calendar.get_events
    target:
      entity_id: calendar.raccolta_rifiuti_via_nomentana_44
    data:
      start_date_time: "{{ today_at('00:00') + timedelta(days=1) }}"
      end_date_time: "{{ today_at('00:00') + timedelta(days=2) }}"
    response_variable: domani
  - variables:
      eventi: "{{ domani['calendar.raccolta_rifiuti_via_nomentana_44'].events }}"
  - condition: template
    value_template: "{{ eventi | count > 0 }}"
  - action: notify.notify
    data:
      title: "🗑️ Domani si raccoglie"
      message: >-
        {% for e in eventi %}{{ e.summary }} entro le {{ as_datetime(e.start).strftime('%H:%M') }}{{ '\n' if not loop.last }}{% endfor %}
```

Preferisci un avviso poco prima della scadenza? Usa il trigger `calendar` con un `offset`, per esempio `"-01:00:00"` per un'ora prima.

## 🔔 Notifica sul telefono quando AMA cambia giorni o orari

Quando il controllo periodico trova un cambiamento, l'integrazione aggiorna il calendario e crea una **notifica dentro Home Assistant**: la vedi nel campanello 🔔 della barra laterale, con il titolo *"AMA Roma: calendario cambiato"*.

> ⚠️ **Questa notifica non arriva da sola sul telefono.** Per riceverla lì devi creare questa automazione.

In **Impostazioni → Automazioni e scene → Crea automazione → ⋮ → Modifica in YAML**, incolla:

```yaml
alias: Avviso cambio calendario AMA
triggers:
  - trigger: persistent_notification
    update_type:
      - added
conditions:
  - condition: template
    value_template: "{{ trigger.notification.title.startswith('AMA Roma') }}"
actions:
  - action: notify.notify
    data:
      title: "{{ trigger.notification.title }}"
      message: "{{ trigger.notification.message }}"
```

Sostituisci `notify.notify` con il servizio del tuo telefono, per esempio `notify.mobile_app_iphone_di_mario` (lo trovi in **Strumenti per sviluppatori → Azioni** cercando `notify.mobile_app`).

## ❓ Domande frequenti

**Non trova la mia via.** Scrivila come sul sito AMA, con il tipo di strada: `via`, `viale`, `piazza`…

**"AMA non ha un calendario per questo civico".** Prova lo stesso indirizzo sul [sito AMA](https://www.amaroma.it/it/servizi/calendario-svuotamento-contenitori): se non lo trova neanche lì, l'indirizzo non è coperto.

**Festività e scioperi?** Non sono inclusi: AMA pubblica solo il calendario settimanale.

## ⚠️ Nota

Integrazione non ufficiale, non collegata ad AMA S.p.A. Usa un servizio web non documentato di amaroma.it: se AMA lo cambia, l'integrazione potrebbe smettere di funzionare finché non viene aggiornata. Problemi? [Apri una segnalazione](https://github.com/woody4165/ha-amaroma/issues).
