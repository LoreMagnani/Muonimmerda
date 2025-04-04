# Analizza i file .root prodotti dal codicino di analisi in cpp
# Si aspetta di trovare il file .xml nella cartella ./xmlfile
# Crea il rootfile nella cartella ./rootfile

import uproot
import numpy as np 
import os
import sys
import awkward as ak
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

# Funzione per cercare e aprire il rootfile
def apri_root_file(nome):
    # Percorso completo con espansione del tilde (~)
    file_path = os.path.expanduser(f"./rootfile/{nome}.root")

    # Apriamo il file ROOT
    try:
        file = uproot.open(file_path)
        print(f"✅ File '{nome}.root' aperto con successo!")
        return file
    except FileNotFoundError:
        print(f"❌ Errore: Il file '{nome}.root' non esiste in {file_path}.")
        sys.exit(1)

def main():
    # Se non passiamo il secondo argomento mi da errore
    if len(sys.argv) < 2:
        print("❌ Errore: Devi specificare il nome del file ROOT.")
        print("Uso: python3 Analisi.py nome_del_file_senza_estensione")
        sys.exit(1)

    # Apriamo il file con il nome passato a terminale
    nome_file = sys.argv[1]

    file = apri_root_file(nome_file)
    tree = file["DigiTree"]

    # Entriamo nella branch ID e salviamo l'Id dell'evento
    event_id = tree["EventId"].array()

    ## Entriamo nel ch. 0 e salviamo i dati in un array
    channel0 = tree["Channel0"].array()

    ## Entriamo nel ch. 1 e salviamo i dati in un array
    channel1 = tree["Channel1"].array()

    ## Entriamo nel ch. 2 e salviamo i dati in un array
    channel2 = tree["Channel2"].array()

    ## Entriamo nel ch. 3 e salviamo i dati in un array
    channel3 = tree["Channel3"].array()

    ### Analisi
    
    tutti_ev = [] #Salverà tutti gli eventi come sequenze di liste di 3 elementi: [id_evento , posizione start , posizione stop]
    tutti_up = []
    tutti_dawn = []
    ev_up = 0
    ev_dawn = 0
    
    for i in range(len(event_id)):
        peaks0 , props0 = find_peaks(-channel0[i] , height = -2900 , prominence = 1000)
        peaks1 , props1 = find_peaks(-channel1[i] , height = -2900 , prominence = 1000)

        #cpprint(peaks0 , peaks1)

        if len(peaks0) == 1 and len(peaks1) == 1:
            array_fin = [event_id[i]] + peaks0.tolist() + peaks1.tolist()
            ev_dawn += 1
            tutti_dawn.append(array_fin)
            tutti_ev.append(array_fin)

        if len(peaks0) == 0 and len(peaks1) == 2:
            array_fin = [event_id[i]] + peaks1.tolist()
            ev_up += 1
            tutti_up.append(array_fin)
            tutti_ev.append(array_fin)

    print(f"eventi up = {ev_up}\neventi dawn = {ev_dawn}\n")
    #print(tutti_ev)

    diff = []
    for j in range(len(tutti_ev)):
        diff.append(abs(tutti_ev[j][2] - tutti_ev[j][1]))
    print(diff)

    # Crea istogramma per titti gli eventi
    plt.hist([diff], bins = 2750, alpha = 0.7, color='b', edgecolor='black')
    plt.xlabel("Tempo")
    plt.ylabel("Counts")
    
    # Creazione della directory di output se non esiste
    output_dir = "./Fina_na_lfile"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{nome_file}.pdf")
    
    # Salvataggio dell'istogramma in formato PDF
    plt.savefig(output_file)
    print(f"Istogramma salvato in: {output_file}")
    plt.show()

    ## Istogrammi aggiuntivi

    ## Funzioni aggiuntive per ch3 e ch4
    #for j in range(len(event_id)):
        



    return

#----------------------------
if __name__ == "__main__":
    main()

