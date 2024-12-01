import argparse
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from scipy.optimize import curve_fit
import muonimmerda

# Funzione principale
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera grafico con fit da un file .ods")
    parser.add_argument("file_name", type=str, help="Nome file (es. Lab_Nucleare)")
    parser.add_argument("page_name", type=str, help="Nome della pagina all'interno del file (es. Partenope)" )
    parser.add_argument("num_graphs", type=int, help="Numero di grafici da generare")
    parser.add_argument("bottom_row", type=int, help="Numero di riga iniziale (es. 43)")
    parser.add_argument("top_row", type=int, help="Numero di riga finale (es. 54)")
    parser.add_argument("output_filename_prefix", type=str, help="Prefisso per il nome dei file di output")
    parser.add_argument("--lungo", type=int, default=4, help="Lunghezza minima plateau (default: 4)")
    parser.add_argument("--plateau", action="store_true", help="Impostare se si vuole anche cercare il plateau (default: no)") 
    parser.add_argument("--unico", action="store_true", help="Impostare se si vuole tutti i plot nello stesso grafico (default: no)")       
    args = parser.parse_args()

    # Verifica se tutti gli argomenti sono presenti
    if args.num_graphs is None or args.top_row is None or args.bottom_row is None:
        print("Errore: tutti gli argomenti sono obbligatori.")
        print("Utilizzo: python3 test.py file_name page_name num_graphs bottom_row top_row output_filename_prefix [--lungo] [--plateau] [--unico]")    
    else:
        file_name = args.file_name
        page_name = args.page_name
        bottom_row = args.bottom_row - 6  # Converte riga finale in indice base zero
        top_row = args.top_row - 6  # Converte riga iniziale in indice base zero
        num_graphs = args.num_graphs
        output_filename_prefix = args.output_filename_prefix
        lungo = args.lungo
        plateau = args.plateau
        unico = args.unico 

        # Percorso completo del file
        file_path = './' + f'{file_name}' + '.ods'


        ## Debug: stampa i dati letti dalla pagina
        #data = muonimmerda.read_ods_page(file_path, page_name)
        #print(f"Dati letti dalla pagina '{page_name}':")
        #for idx, row in enumerate(data, start=1):
        #    print(f"Riga {idx}: {row}") 

        
        if unico: 
            muonimmerda.unicum(file_path, page_name, bottom_row, top_row, output_filename_prefix, num_graphs)
        else:
            # Genera i grafici
            for i in range(1, num_graphs + 1):     # Creazione dei grafici per ogni colonna successiva alla A
                print(i, "-esimo ciclo")
                if page_name == "CPA":
                    muonimmerda.CPA(file_path, page_name, bottom_row, top_row, i, lungo)
                elif plateau:
                    muonimmerda.find_plateau(file_path, page_name, bottom_row, top_row, i, lungo)
                else:
                    muonimmerda.save_graph(file_path, page_name, bottom_row, top_row, output_filename_prefix, i)
