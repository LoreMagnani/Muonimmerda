import argparse
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from scipy.optimize import curve_fit
import muonimerde

# Funzione principale
if __name__ == "__main__":
    # Opzioni alla chiamata
    parser = argparse.ArgumentParser(description="Genera grafico con fit da un file .ods")
    parser.add_argument("--l", action="store_true", help="Impostare se sei il coglione che usa linux") 
    parser.add_argument("file_path", type=str, help="Percorso file")
    parser.add_argument("page_name", type=str, help="Nome della pagina all'interno del file (es. Partenope)" )
    parser.add_argument("num_graphs", type=int, help="Numero di grafici da generare")
    parser.add_argument("start_row", type=int, help="Numero di riga iniziale (es. 43)")
    parser.add_argument("end_row", type=int, help="Numero di riga finale (es. 54)")
    parser.add_argument("--plateau", action="store_true", help="Impostare se vuoi fittare il plateau") 
    parser.add_argument("--lungo", type=int, default=4, help="Lunghezza minima plateau (default: 4)")

    args = parser.parse_args()

    # Salva variabili
    l = args.l
    file_path = args.file_path
    page_name = args.page_name
    start_row = args.start_row 
    end_row = args.end_row 
    num_graphs = args.num_graphs
    plateau = args.plateau
    lungo = args.lungo


    for i in range(1, num_graphs + 1):
        # Prende le variabili principali
        if l:
            soglie, counts, nome_rivelatore, voltaggio = muonimerde.trova_dati_per_il_coglione_con_linux(file_path, start_row, end_row, i, page_name)
        else:
            soglie, counts, nome_rivelatore, voltaggio = muonimerde.trova_dati_odf(file_path, start_row, end_row, i, page_name)

        if plateau:
            muonimerde.fit_plateau()
        else:
            # Fa solo il plot
            muonimerde.solo_plot(soglie, counts, nome_rivelatore, voltaggio)
            
