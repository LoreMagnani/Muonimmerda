# Rubiamo dati, daje
# Sfrutta il mio filesistem, non adatto su altri

import Analisi_root

import ROOT
import os
import numpy as np
import scipy.signal as sig
import ctypes
from tkinter import filedialog, simpledialog, Tk
from datetime import datetime, timedelta
import argparse
import time

# Cerco il file da cui ladrare dati
def tova_nomi_associati(nomefile):
    titolo_loro = {
        "test_alluminio" : "Alluminio_loro" ,
        "Sale_test" : "Sale_loro" ,
        #"Pasquatot" : ""  --> da scaricare
    }.get(nomefile)
    if titolo_loro:
        path_loro = f"~/Scrivania/Muoni/Isis/rootfile/{titolo_loro}/{titolo_loro}_1.root" 
        return path_loro
    else:
        return

def quanto_vuoi_essere_una_merda():
    root = Tk(); root.withdraw()
    s = simpledialog.askinteger("Sei una merda", "Ma di preciso, quanto vuoi esserlo? (int)")
    root.destroy()
    if s and s>0:
        return s
    else:
        print("Hai scelto di non fare il merda, bravo")
        return 0

# Processa un singolo file ROOT e restituisce le differenze
def process_merdata(files_loro):
    print("inizio a fare la merda")
    dim_max = quanto_vuoi_essere_una_merda()

    file = ROOT.TFile.Open(files_loro)
    tree = file.Get("DigiTree")

    tutti_ev, tutti_up, tutti_dawn = [], [], []
    n_entries = int(tree.GetEntries())
    if (dim_max > n_entries):
        dim_max = n_entries
    for i in range(dim_max):
        tree.GetEntry(i)
        event_id = int(tree.EventId)
        ch0 = np.array(tree.Channel0)
        ch1 = np.array(tree.Channel1)
        ch2 = np.array(tree.Channel2)
        ch3 = np.array(tree.Channel3)
        clock = float(tree.EventTime)
   
        p0, _ = sig.find_peaks(-ch0, height = -3000, prominence = 750)
        p2, _ = sig.find_peaks(-ch2, height = -3000, prominence = 750)

        # Alternativa è np.gradient
        if len(p0) == 1 and len(p2) == 1:
            e = [event_id] + p0.tolist() + p2.tolist() + [clock]
            tutti_dawn.append(e)
            tutti_ev.append(e)

        elif len(p0) == 2 and len(p2) == 0:
            e = [event_id] + p0.tolist() + [clock]
            tutti_up.append(e)
            tutti_ev.append(e)

    diffs = {
        'all':  [4 * abs(e[2] - e[1]) for e in tutti_ev],
        'up':   [4 * abs(e[2] - e[1]) for e in tutti_up],
        'dawn': [4 * abs(e[2] - e[1]) for e in tutti_dawn],
        'clock': [e[3] for e in tutti_ev]
    }
    return diffs

# Funzione principale: unisce tutti i file se cartella, o singolo
def analizza_root(path, bin_dict, fit_params, fit_params_limit, foc, plot_updown, clock, fondo):
    # Accumulatori globali di diff
    accum = {'all': [], 'up': [], 'dawn': [], 'clock': []}

    if foc == "file":
        diffs = Analisi_root.process_file_diffs(path)
        nomefile = os.path.splitext(os.path.basename(path))[0]
        for t in accum: accum[t].extend(diffs[t])
    elif foc == "cartella":
        files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.root')]
        nomefile = os.path.basename(path.rstrip('/\\'))
        # Troviamo dati aggiuntivi
        files_loro = tova_nomi_associati(nomefile)
        for fpath in files:
            print("Elaboro:", fpath)
            diffs = Analisi_root.process_file_diffs(fpath)
            for t in accum: accum[t].extend(diffs[t])
        print("Elaboro la merdata")
        diffs_loro = process_merdata(files_loro)
        for t in accum: accum[t].extend(diffs_loro[t])
    else:
        print("Modalità non riconosciuta.")
        return
    
    if clock:
        Analisi_root.plotClock(accum['clock'], nomefile)

    # Ora un unico plot per ciascun tipo
    for tipo in ['all', 'up', 'dawn']:
        if tipo == 'all' or (plot_updown and tipo in ['up', 'dawn']):
            Analisi_root.plot_e_fit(accum[tipo], tipo, nomefile, bin_dict, fit_params, fit_params_limit, fondo, accum['clock'])

# GUI ROOT con TApplication
def root_gui(ud, clock):
    # Scelta file o cartella
    foc, path = Analisi_root.scegli_f_o_c()
    if not foc or not path:
        print("Nessuna analisi eseguita.")
        return

    fondo = Analisi_root.file_fondo()

    # Parametri preimpostati
    bin_dict = {"all":{'bins':100,'start':5}, "up":{'bins':100,'start':5}, "dawn":{'bins':100,'start':5}}
    fit_params = {'auto':True, 'a':100, 'b':5, "A":50, "B":50 , "C":10, "#tau_{free}":2200, "#tau_{NaCl}":850, '#tau_{Al}':880}
    fit_params_limit = {'auto':True, '#tau_{free}_sup':2300, '#tau_{free}_inf':2100, '#tau_{NaCl}_sup':1200, '#tau_{NaCl}_inf':500, '#tau_{Al}_sup':960, '#tau_{Al}_inf':800}

    # Chiede se vuoi cambiare parametri
    root = Tk(); root.withdraw()
    ans = simpledialog.askstring("Parametri","Modifica parametri? (s/n)")
    root.destroy()
    if ans and ans.lower().startswith('s'):
        panel, entries = Analisi_root.crea_pannello_parametri(bin_dict, fit_params, fit_params_limit)
        #app.Run()  # attende OK
        # leggi valori
        for k,e in entries.items():
            v = e.GetNumber()
            if k in fit_params: fit_params[k]=v
            elif k in fit_params_limit: fit_params_limit[k]=v
            else:
                dk,sk = k.rsplit('_',1)
                bin_dict[dk][sk]=int(v)

    if foc and path:
        analizza_root(path, bin_dict, fit_params, fit_params_limit, foc, ud, clock, fondo)
        app.Run()
    else:
        print("Nessuna analisi eseguita.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisi file .root")
    parser.add_argument("--clock", action="store_true", help="Plotta la distribuzione nel tempo dei muoni")
    parser.add_argument("--ud", action="store_true", help="Mostra anche i plot separati per up e dawn")
    args = parser.parse_args()

    ud = args.ud
    clock = args.clock

    #print("ciao")

    ROOT.gROOT.SetBatch(False)
    if not hasattr(ROOT, 'gApplication') or not ROOT.gApplication:
        app = ROOT.TApplication("app", 0, ctypes.c_void_p())
    else:
        app = ROOT.gApplication

    root_gui(ud, clock) 
