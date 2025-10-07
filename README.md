# BankInzicht

BankInzicht is een Python-applicatie waarmee je eenvoudig overzichten en grafieken maakt van CSV-uitreksels van je bankafschriften. 

## Features

### Ondersteunde banken
- **ING**
- **Rabobank**

### Overzichten en Analyses
- **Maandelijkse overzichten** - Inkomsten, uitgaven en netto per maand
- **Tegenpartij analyse** - Overzicht per tegenpartij met netto bedragen
- **Label categorisering** - Groepeer transacties op eigen labels
- **Zakelijk/Privé scheiding** - Filter en analyseer zakelijke vs. privé uitgaven
- **Grafieken** - Visuele weergave van financiële data

### Functionaliteiten
- **Automatische IBAN filtering** - Interne overboekingen worden automatisch gefilterd
- **Configureerbare negeerlijst** - Sluit bepaalde tegenpartijen uit via `settings.toml` (bijvoorbeeld je eigen spaarrekening)
- **Persistent labeling** - Labels worden opgeslagen in de database los van CSV-bestanden

## Installatie

### Automatische installatie (Windows)
1. Download of clone dit project
2. Dubbelklik op `setup.bat`

### CSV-bestanden toevoegen
- Plaats je bankafschrift CSV-bestanden in de `/data` map
- De applicatie detecteert automatisch het bank-formaat (indien ondersteund)
- Meerdere bestanden kunnen tegelijk worden verwerkt
