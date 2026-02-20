# Guida Git per Rafting Republic

## Configurazione Iniziale
Hai ricollegato il progetto al nuovo repository: `https://github.com/RaftingRepublic/gesionaleRRv4.git`

## Comandi Principali per Lavorare in Due

### 1. PRIMA di iniziare a lavorare (IMPORTANTE)
Sempre, appena accendi il PC o prima di scrivere codice, scarica le modifiche del tuo collega:
```bash
git pull
```
*Se ci sono conflitti, git te lo dirà. Se tutto va bene, sei aggiornato.*

### 2. Controllare cosa hai modificato
Prima di salvare, guarda cosa hai cambiato:
```bash
git status
```
*Ti mostra i file modificati in rosso.*

### 3. Salvare le modifiche
Quando hai finito un pezzo di lavoro (o una feature):

1. **Aggiungi i file:**
   ```bash
   git add .
   ```
   *(Il punto indica "tutti i file modificati")*

2. **Crea il commit (salvataggio locale):**
   ```bash
   git commit -m "Descrizione breve di cosa hai fatto"
   ```
   *Esempio: `git commit -m "Aggiunto filtro per data"`*

3. **Invia al server (GitHub):**
   ```bash
   git push
   ```

## Gestione dei Conflitti (Quando lavorate sugli stessi file)
Se tu e il tuo collega modificate le STESSE righe dello STESSO file contemporaneamente:
1. `git pull` ti darà errore.
2. Apri i file con conflitto (VS Code li evidenzia).
3. Scegli quali modifiche tenere (le tue, le sue, o entrambe).
4. Salva il file.
5. Fai `git add .`, `git commit` e `git push`.

## Regole d'Oro
1. **Fai `git pull` spesso.** Meno tempo passa, meno conflitti avrai.
2. **Fai commit piccoli e frequenti.** È più facile capire cosa è successo se qualcosa si rompe.
3. **Non usare `--force`** a meno che tu non sappia ESATTAMENTE cosa stai facendo (cancella il lavoro degli altri).

## Gestione Multi-Remote (Salvare su entrambi gli account)
Ho già configurato per te i due collegamenti:
1. **origin** -> `RaftingRepublic/gesionaleRRv4` (Il nuovo principale)
2. **proto** -> `Theollotti/ProtoGRR_V1` (Il vecchio backup)

### Come inviare le modifiche (Push)
Per essere sicuro che il codice sia salvato su entrambi, esegui questi due comandi in sequenza:

```bash
git push origin main
git push proto main
```

*Se uno dei due fallisce (es. repository non trovato), l'altro potrebbe comunque funzionare.*
