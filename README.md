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
| 📅 **Calendario automatico** | Un evento per ogni raccolta: *Carta*, *Organico*, *Plastica e metalli*, *Indifferenziato*, *Vetro* |
| ⏰ **Orari giusti** | Porta a porta: *"Esporre entro le 20:00"*. Cassonetti in strada: *"Svuotamento 22:00–04:00"* |
| 🔄 **Sempre aggiornato** | Ogni 30 giorni (e a ogni riavvio) ricontrolla il sito AMA |
| 🔔 **Ti avvisa dei cambi** | Se AMA modifica giorni o orari, il calendario si aggiorna e ricevi una notifica |
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

- **`on`** oggi c'è una raccolta (l'evento dura tutta la giornata);
- **`off`** oggi non c'è nessuna raccolta.

Gli attributi dell'entità mostrano la **prossima raccolta**: `message` (il tipo di rifiuto), `description` (l'orario), `start_time`.

## 🔔 Esempio: avviso la sera prima

```yaml
alias: Promemoria spazzatura
triggers:
  - trigger: calendar
    event: start
    entity_id: calendar.raccolta_rifiuti_via_nomentana_44
    offset: "-04:00:00"   # alle 20:00 del giorno prima
actions:
  - action: notify.notify
    data:
      title: "🗑️ Domani si raccoglie"
      message: "{{ trigger.calendar_event.summary }}: {{ trigger.calendar_event.description }}"
```

## ❓ Domande frequenti

**Non trova la mia via.** Scrivila come sul sito AMA, con il tipo di strada: `via`, `viale`, `piazza`…

**"AMA non ha un calendario per questo civico".** Prova lo stesso indirizzo sul [sito AMA](https://www.amaroma.it/it/servizi/calendario-svuotamento-contenitori): se non lo trova neanche lì, l'indirizzo non è coperto.

**Il vetro non compare.** In molte zone il vetro si porta sempre nelle campane verdi in strada, quindi non ha un giorno di raccolta.

**Festività e scioperi?** Non sono inclusi: AMA pubblica solo il calendario settimanale.

## ⚠️ Nota

Integrazione non ufficiale, non collegata ad AMA S.p.A. Usa un servizio web non documentato di amaroma.it: se AMA lo cambia, l'integrazione potrebbe smettere di funzionare finché non viene aggiornata. Problemi? [Apri una segnalazione](https://github.com/woody4165/ha-amaroma/issues).
