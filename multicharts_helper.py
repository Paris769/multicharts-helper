"""Helper per la generazione di strategie PowerLanguage da utilizzare in MultiCharts.

Questo modulo contiene funzioni che permettono di generare codice PowerLanguage
e salvare i file su disco. Ã¨ pensato come supporto per chi utilizza MultiCharts
e desidera creare velocemente un segnale (strategy) parametrico da importare
nell’Editor PowerLanguage.

MultiCharts supporta l’importazione di studi in vari formati, tra cui PLA, ELA,
ELS, ELD e XML【458576677552250†L114-L140】. L’importazione avviene tramite l’Editor
PowerLanguage: menu **File > Importa**. Spuntando l’opzione «Compila durante
l’importazione» si può compilare automaticamente lo studio【458576677552250†L147-L165】.

Una volta importato, il segnale può essere applicato ad un grafico storico e
MultiCharts calcola il backtest bar after bar, generando ordini e
registrando le performance【844032993114593†L114-L134】. L’ottimizzazione dei
parametri avviene dalla finestra di ottimizzazione, dove è possibile scegliere
tra una ricerca esaustiva o genetica【844032993114593†L135-L154】.

Nota importante: questo script **non interagisce** con MultiCharts. Per
automatizzare l’interfaccia grafica di MultiCharts Ã¨ necessario utilizzare
librerie di automazione su Windows (ad esempio `pywinauto`) e avere MultiCharts
installato. Le funzioni qui presenti si limitano a generare codice sorgente.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent

def generate_powerlanguage_signal(name: str, code_body: str) -> Path:
    """Crea un file `.txt` contenente un segnale PowerLanguage.

    Parameters
    ----------
    name : str
        Nome del segnale/strategia. VerrÃ  utilizzato come nome del file.
    code_body : str
        Corpo del codice PowerLanguage da includere nel file. Deve includere la
        dichiarazione di inputs e il codice della strategia.

    Returns
    -------
    Path
        Percorso del file generato.

    Example
    -------
    >>> code = "inputs: Length(14); ..."
    >>> generate_powerlanguage_signal("MyStrategy", code)
    PosixPath('MyStrategy.txt')
    """
    filename = f"{name}.txt"
    path = Path(filename)
    # Includiamo commento iniziale con istruzioni di importazione
    header = dedent(
        f"""
        // File generato automaticamente
        // Nome del segnale: {name}
        // Istruzioni:
        //   - Importare questo file nell'Editor PowerLanguage (File > Importa) e spuntare
        //     l'opzione "Compila durante l'importazione"【458576677552250†L147-L165】.
        //   - Applicare il segnale ad un grafico storico per eseguire il backtest【844032993114593†L114-L134】.
        //   - Per ottimizzare i parametri, aprire la finestra di ottimizzazione (Formato > Segnali > Ottimizza)
        //     e scegliere la modalitÃ  di ricerca (esaustiva o genetica)【844032993114593†L135-L154】.
        """
    ).strip()
    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n\n")
        f.write(code_body.strip() + "\n")
    return path

def ma_crossover_strategy(name: str, fast_length: int, slow_length: int) -> str:
    """Genera codice PowerLanguage per una strategia di incrocio di medie mobili.

    La strategia utilizza due medie mobili esponenziali e genera un segnale long
    quando la media veloce incrocia sopra la media lenta e un segnale short
    quando la media veloce incrocia sotto la media lenta.

    Parameters
    ----------
    name : str
        Nome della strategia (solo usato per commenti).
    fast_length : int
        Periodo della media mobile veloce.
    slow_length : int
        Periodo della media mobile lenta.

    Returns
    -------
    str
        Una stringa con il codice PowerLanguage.

    Notes
    -----
    Il codice include gli `inputs` per le lunghezze delle medie in modo da
    poter essere ottimizzati tramite la funzione di ottimizzazione di MultiCharts
    (impostando i valori di inizio/fine/step nella finestra di ottimizzazione
    della piattaforma). La funzione `SetCustomFitnessValue` non viene usata,
    lasciando che la piattaforma calcoli gli indici di performance predefiniti【844032993114593†L135-L156】.
    """
    # Template PowerLanguage: definizione di inputs e logica trading
    code = dedent(
        f"""
        // Strategia: {name}
        inputs: FastLength({fast_length}), SlowLength({slow_length});

        vars: fastMA(0), slowMA(0);

        // Calcolo medie mobili esponenziali
        fastMA = XAverage(Close, FastLength);
        slowMA = XAverage(Close, SlowLength);

        // Regole di ingresso long/short
        if (fastMA crosses over slowMA) then
            begin
                buy ("LongEntry") next bar at market;
            end;
        if (fastMA crosses under slowMA) then
            begin
                sellshort ("ShortEntry") next bar at market;
            end;

        // Regole di uscita: invertendo la posizione quando avviene incrocio opposto
        if MarketPosition = 1 and fastMA crosses under slowMA then
            begin
                sell ("ExitLong") next bar at market;
            end;
        if MarketPosition = -1 and fastMA crosses over slowMA then
            begin
                buytocover ("ExitShort") next bar at market;
            end;
        """
    ).strip()
    return code



def main(args: list[str] | None = None) -> None:
    """Punto d’ingresso per eseguire la generazione da linea di comando.

    Usa argparse per ricevere il nome della strategia e le lunghezze delle medie
    mobili e genera un file `.txt` nella cartella corrente. Questa funzione
    permette di usare il modulo come script eseguibile.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Genera un file PowerLanguage per una strategia di incrocio di medie mobili. "
            "Importare il file risultante in MultiCharts per compilazione, backtest e ottimizzazione."
        )
    )
    parser.add_argument("--name", required=True, help="Nome del segnale/strategia")
    parser.add_argument("--fast", type=int, default=14, help="Periodo della media mobile veloce (default 14)")
    parser.add_argument("--slow", type=int, default=30, help="Periodo della media mobile lenta (default 30)")
    ns = parser.parse_args(args)

    # Genera codice e file
    code = ma_crossover_strategy(ns.name, ns.fast, ns.slow)
    file_path = generate_powerlanguage_signal(ns.name, code)
    print(f"Creato file: {file_path.resolve()}")


if __name__ == "__main__":
    main()
