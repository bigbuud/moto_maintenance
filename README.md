# Moto Onderhoud (Home Assistant, HACS)

Onderhoudsplanner voor je motor als Home Assistant custom integration. Je houdt de kilometerstand bij, registreert uitgevoerd onderhoud en krijgt meldingen wanneer een beurt bijna of echt aan de beurt is.

## Taken (standaardintervallen)

| Taak | km | maanden |
|---|---|---|
| Olie vervangen | 6000 | 12 |
| Oliefilter vervangen | 6000 | 12 |
| Ketting bijstellen | 1000 | 3 |
| Ketting insmeren | 500 | 2 |
| Luchtfilter | 12000 | 24 |
| Bougies | 12000 | 24 |
| Groot onderhoud (dealer) | 12000 | 12 |

Dit zijn **voorbeeldwaarden**. Pas ze per taak aan via de interval-entiteiten (zie hieronder) volgens het onderhoudsboekje van je motor. Interval `0` schakelt dat criterium uit (bv. enkel op tijd).

## Installatie via HACS

1. Maak de GitHub-repo **public**. Geef ze een beschrijving en een paar topics (bv. `home-assistant`, `hacs`, `motorcycle`). HACS vereist dat.
2. Maak een release, bv. tag `v0.1.0` (anders gebruikt HACS de laatste commit).
3. Home Assistant → HACS → drie puntjes → **Aangepaste repositories** → URL van de repo, categorie **Integratie**.
4. Download **Moto Onderhoud** en herstart Home Assistant.
5. Instellingen → Apparaten & services → **Integratie toevoegen** → *Moto Onderhoud*. Geef de motor een naam, vul de kilometerstand in en optioneel een notify-service (bv. `notify.mobile_app_jouw_gsm`).

Handmatig kan ook: kopieer `custom_components/moto_onderhoud` naar de map `custom_components` van je HA-config.

## Entiteiten (per motor, gegroepeerd onder één apparaat)

| Entiteit | Doel |
|---|---|
| `number` Kilometerstand | Huidige stand, zelf bijwerken |
| `sensor` per taak | Status: `ok`, `binnenkort`, `achterstallig`, `onbekend` |
| `button` per taak ("uitgevoerd") | Registreert de taak op de huidige kilometerstand en de datum van vandaag |
| `text` per taak ("notitie") | Vrije notitie (max. 255 tekens): type filter, prijs, merk olie, ... |
| `number` per taak (interval km / maanden) | Intervallen aanpassen (categorie *Configuratie*) |

Sensorattributen: `km_remaining`, `days_remaining`, `last_km`, `last_date`, `interval_km`, `interval_months`, `note`.
Een taak is **binnenkort** bij minder dan 300 km of 14 dagen te gaan (instelbaar in de opties) en **achterstallig** bij 0 of minder. Zolang je geen datum hebt geregistreerd, staat een taak op `onbekend`.

## Beginwaarden instellen

Registreer per taak je laatste beurt met de service `moto_onderhoud.register_maintenance` (Ontwikkelaarstools → Acties), gericht op de taaksensor:

```yaml
action: moto_onderhoud.register_maintenance
target:
  entity_id: sensor.motor_olie_vervangen
data:
  km: 12500
  date: "2026-04-15"
  note: "Motul 7100 10W40, filter HF204, 85 euro"
```

`km`, `date` en `note` zijn optioneel (leeg = huidige stand, vandaag, vorige notitie behouden). De entiteit-ID hangt af van de naam die je de motor gaf.

## Meldingen

- Direct bij overgang naar `binnenkort` of `achterstallig`, via de ingestelde notify-service.
- Dagelijks om 09:00 een herinnering voor alles wat achterstallig is.
- Bij elke overgang wordt ook het event `moto_onderhoud_task_due` afgevuurd (met `motor`, `name`, `status`, `km_remaining`, `days_remaining`), zodat je eigen automations kunnen reageren.

Notify-service en drempels wijzig je later via Instellingen → Apparaten & services → Moto Onderhoud → **Configureren**.

## Dashboard

Zie `examples/dashboard.yaml` voor een overzichtstabel. Knoppen en notities voeg je toe met een Entiteiten-kaart.

## Opmerkingen

- Gegevens worden lokaal opgeslagen in `.storage/moto_onderhoud.<entry_id>`.
- De kilometerstand is handmatig; er is geen koppeling met de motor.
