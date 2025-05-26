# Come Analisi_root.py ma la logica è questa: Per ogni ID controllo se c'è un evento in ch.1, nel caso controllo che ch.0 e ch.2 abbiano esattamente un evento ciascuno
# Solstanzialmente alla mia logica aggiungo il controllo che ci sia un evento nel ch1

import ROOT
import os
import numpy as np
import scipy.signal as sig
import ctypes
from tkinter import filedialog, simpledialog, Tk
from datetime import datetime, timedelta
import argparse

ROOT.gStyle.SetOptFit(1111)

# keepalive con scope globale per evitare GC prematuro
_active_canvases = []
_active_panels   = []

# Funzione di fit esponenziale (se serve altrove)
def d_exp_func(x, par):
    return par[0] * np.exp(-x / par[1]) + par[2] + par[3] * np.exp(-x / par[4])

# Processa un singolo file ROOT e restituisce le differenze
def process_file_diffs(filepath):
    print("inizio a processare")

    file = ROOT.TFile.Open(filepath)
    tree = file.Get("DigiTree")

    tutti_ev, tutti_up, tutti_dawn = [], [], []
    n_entries = int(tree.GetEntries())

    #DEBUG
    #UP = 0
    #DAWN  = 0
    p3_0 = 0
    p3_1 = 0
    p3_2 = 0
    p3_mag = 0
    for i in range(n_entries):
        tree.GetEntry(i)
        event_id = int(tree.EventId)
        ch0 = np.array(tree.Channel0)
        ch1 = np.array(tree.Channel1)
        ch2 = np.array(tree.Channel2)
        ch3 = np.array(tree.Channel3)
    
        p0, _ = sig.find_peaks(-ch0, height = -3000, prominence = 750)
        p1, _ = sig.find_peaks(-ch1, height = -3000, prominence = 750)
        p2, _ = sig.find_peaks(-ch2, height = -3000, prominence = 750)
        p3, _ = sig.find_peaks(-ch3, height = -3000, prominence = 750)

    #    if len(p0) == 0:
    #        p3_0 += 1
    #    elif len(p0) == 1:
    #        p3_1 += 1
    #    elif len(p0) == 2:
    #        p3_2 += 1
    #    else:
    #        p3_mag += 1

        # Alternativa è np.gradient

        #if len(p2) == 1:
        if len(p0) == 1 and len(p2) == 1:
            e = [event_id] + p0.tolist() + p2.tolist()
            tutti_dawn.append(e)
            tutti_ev.append(e)
    #        DAWN += 1
        elif len(p0) == 2 and len(p2) == 0:
            e = [event_id] + p0.tolist()
            tutti_up.append(e)
            tutti_ev.append(e)
    #        UP += 1

    #print(tutti_ev)
    #print(UP, DAWN)

    # Calcola differenze (4*(t1-t0))
    diffs = {
        'all':  [4 * abs(e[2] - e[1]) for e in tutti_ev],
        'up':   [4 * abs(e[2] - e[1]) for e in tutti_up],
        'dawn': [4 * abs(e[2] - e[1]) for e in tutti_dawn],
    }
    return diffs

# Funzione di plotting e fitting con ROOT
def plot_e_fit(diff, tipo, nomefile, bin_dict, fit_params, fit_params_limit):
    bins      = bin_dict[tipo]['bins']
    start_bin = bin_dict[tipo]['start']
    x_max     = max(diff)

    # Istogramma ROOT
    hist = ROOT.TH1F(f"hist_{tipo}", f"Fit {tipo} - {nomefile}", bins, 0, x_max)
    for val in diff:
        hist.Fill(val)

    # Definizione delle due funzioni di fit
    fit_3p = ROOT.TF1(f"fit3_{tipo}", "[0]*exp(-x/[1]) + [2]", 0, x_max)
    fit_3p.SetParName(0, "a")
    fit_3p.SetParName(1, "#tau_{free}")
    fit_3p.SetParName(2, "b")
    fit_3p.SetParameters(fit_params['a'], fit_params['#tau_{free}'], fit_params['b'])
    fit_3p.SetParLimits(1, fit_params_limit['#tau_{free}_inf'], fit_params_limit['#tau_{free}_sup'])

    fit_5p_NaCl = ROOT.TF1(f"fit5_NaCl_{tipo}", "[0]*exp(-x/[1]) + [2] + [3]*exp(-x/[4])", 0, x_max)
    fit_5p_NaCl.SetParName(0, "B")
    fit_5p_NaCl.SetParName(1, "#tau_{free}")
    fit_5p_NaCl.SetParName(2, "A")
    fit_5p_NaCl.SetParName(3, "C")
    fit_5p_NaCl.SetParName(4, "#tau_{NaCl}")
    fit_5p_NaCl.SetParameters(fit_params['B'], fit_params['#tau_{free}'], fit_params['A'], fit_params['C'], fit_params['#tau_{NaCl}'])
    fit_5p_NaCl.SetParLimits(4, fit_params_limit['#tau_{NaCl}_inf'], fit_params_limit['#tau_{NaCl}_sup'])
    fit_5p_NaCl.SetParLimits(1, fit_params_limit['#tau_{free}_inf'], fit_params_limit['#tau_{free}_sup'])

    fit_5p_Al = ROOT.TF1(f"fit5_Al_{tipo}", "[0]*exp(-x/[1]) + [2] + [3]*exp(-x/[4])", 0, x_max)
    fit_5p_Al.SetParName(0, "B")
    fit_5p_Al.SetParName(1, "#tau_{free}")
    fit_5p_Al.SetParName(2, "A")
    fit_5p_Al.SetParName(3, "C")
    fit_5p_Al.SetParName(4, "#tau_{Al}")
    fit_5p_Al.SetParameters(fit_params['B'], fit_params['#tau_{free}'], fit_params['A'], fit_params['C'], fit_params['#tau_{Al}'])
    fit_5p_Al.SetParLimits(1, fit_params_limit['#tau_{Al}_inf'], fit_params_limit['#tau_{Al}_sup'])
    fit_5p_Al.SetParLimits(4, fit_params_limit['#tau_{free}_inf'], fit_params_limit['#tau_{free}_sup'])

    # Disegna su canvas
    c = ROOT.TCanvas(f"c_{tipo}", f"Fit {tipo}", 800, 600)
    hist.GetXaxis().SetTitle("Tempo [ns]")
    hist.GetYaxis().SetTitle("Counts")
    hist.SetFillColorAlpha(ROOT.kBlue-7, 0.35)
    hist.Draw("HIST")

    # Panel interattivo senza fit automatico
    panel = hist.FitPanel()

    # Memorizzazione globale
    _active_canvases.extend([c, hist, fit_3p, fit_5p_NaCl, fit_5p_Al])
    _active_panels.append(panel)

    # Aggiorna il canvas
    c.Update()

    outdir = "./Fina_na_lfile"
    if not os.path.exists(outdir): os.makedirs(outdir)
    c.SaveAs(f"{outdir}/{nomefile}_{tipo}.pdf")

# Funzione principale: unisce tutti i file se cartella, o singolo
def analizza_root(path, bin_dict, fit_params, fit_params_limit, foc, plot_updown, clock):
    # Accumulatori globali di diff
    #accum = {'all': [], 'up': [], 'dawn': [], 'clock': []}
    accum = {'all': [], 'up': [], 'dawn': []}

    if foc == "file":
        print("fin qua ci sono")
        diffs = process_file_diffs(path)
        nomefile = os.path.splitext(os.path.basename(path))[0]
        for t in accum: accum[t].extend(diffs[t])
    elif foc == "cartella":
        files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.root')]
        nomefile = os.path.basename(path.rstrip('/\\'))
        for fpath in files:
            print("Elaboro:", fpath)
            diffs = process_file_diffs(fpath)
            for t in accum: accum[t].extend(diffs[t])
    else:
        print("Modalità non riconosciuta.")
        return
    
    # Ora un unico plot per ciascun tipo
    for tipo in ['all', 'up', 'dawn']:
        if tipo == 'all' or (plot_updown and tipo in ['up', 'dawn']):
            plot_e_fit(accum[tipo], tipo, nomefile, bin_dict, fit_params, fit_params_limit)

# Dialogo utente per file o cartella
def scegli_f_o_c():
    root = Tk(); root.withdraw()
    s = simpledialog.askstring("Modalità", "File o Cartella? (f/c)")
    root.destroy()
    if s and s.lower().startswith('f'):
        return 'file', filedialog.askopenfilename(filetypes=[("ROOT files","*.root")])
    elif s and s.lower().startswith('c'):
        return 'cartella', filedialog.askdirectory()
    else:
        return None, None

def crea_pannello_parametri(bin_dict, fit_params, fit_params_limit):
    # Finestra principale
    main = ROOT.TGMainFrame(ROOT.gClient.GetRoot(), 400, 600)
    main.SetWindowName("Impostazione Parametri Fit")
    vframe = ROOT.TGVerticalFrame(main)
    main.AddFrame(vframe, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY))
    entries = {}
    # campi fit_params
    for key, val in fit_params.items():
        h = ROOT.TGHorizontalFrame(vframe)
        h.AddFrame(ROOT.TGLabel(h, key), ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        e = ROOT.TGNumberEntry(h, float(val), 9, -1,
                          ROOT.TGNumberFormat.kNESReal,
                          ROOT.TGNumberFormat.kNEAAnyNumber,
                          ROOT.TGNumberFormat.kNELLimitMinMax)
        e.SetLimitValues(-1e6,1e6)
        h.AddFrame(e, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        vframe.AddFrame(h)
        entries[key] = e
    # campi fit_params_limit
    for p in ['#tau_{free}','#tau_{NaCl}','#tau_{Al}']:
        for b in ['_inf','_sup']:
            k = p+b
            if k in fit_params_limit:
                h = ROOT.TGHorizontalFrame(vframe)
                h.AddFrame(ROOT.TGLabel(h, k), ROOT.TGLayoutHints(ROOT.kLHintsLeft))
                e = ROOT.TGNumberEntry(h, float(fit_params_limit[k]), 9, -1,
                                  ROOT.TGNumberFormat.kNESInteger,
                                  ROOT.TGNumberFormat.kNEAAnyNumber,
                                  ROOT.TGNumberFormat.kNELLimitMinMax)
                e.SetLimitValues(0,10000)
                h.AddFrame(e, ROOT.TGLayoutHints(ROOT.kLHintsRight))
                vframe.AddFrame(h)
                entries[k] = e
    # campi bin_dict
    for dkey, sd in bin_dict.items():
        for sub in ['bins','start']:
            fk = f"{dkey}_{sub}"
            h = ROOT.TGHorizontalFrame(vframe)
            h.AddFrame(ROOT.TGLabel(h, fk), ROOT.TGLayoutHints(ROOT.kLHintsLeft))
            e = ROOT.TGNumberEntry(h, float(sd[sub]), 9, -1,
                              ROOT.TGNumberFormat.kNESInteger,
                              ROOT.TGNumberFormat.kNEAAnyNumber,
                              ROOT.TGNumberFormat.kNELLimitMinMax)
            e.SetLimitValues(0,10000)
            h.AddFrame(e, ROOT.TGLayoutHints(ROOT.kLHintsRight))
            vframe.AddFrame(h)
            entries[fk] = e

    bf = ROOT.TGHorizontalFrame(vframe)
    btn = ROOT.TGTextButton(bf, "OK")
    btn.Connect("Clicked()","TGMainFrame",main,"CloseWindow()")
    # Termina il loop di TApplication per proseguire
    btn.Connect("Clicked()","TApplication",ROOT.gApplication,"Terminate(Int_t)")
    bf.AddFrame(btn,ROOT.TGLayoutHints(ROOT.kLHintsCenterX))
    vframe.AddFrame(bf)
    main.MapSubwindows(); main.Resize(); main.MapWindow()
    return main,entries

# GUI ROOT con TApplication
def root_gui(ud, clock):
    # Scelta file o cartella
    foc, path = scegli_f_o_c()
    if not foc or not path:
        print("Nessuna analisi eseguita.")
        return

    # Parametri preimpostati
    bin_dict = {"all":{'bins':100,'start':5}, "up":{'bins':100,'start':5}, "dawn":{'bins':100,'start':5}}
    fit_params = {'auto':True, 'a':100, 'b':5, "A":50, "B":50 , "C":10, "#tau_{free}":2200, "#tau_{NaCl}":850, '#tau_{Al}':880}
    fit_params_limit = {'auto':True, '#tau_{free}_sup':2300, '#tau_{free}_inf':2100, '#tau_{NaCl}_sup':1200, '#tau_{NaCl}_inf':500, '#tau_{Al}_sup':960, '#tau_{Al}_inf':800}

    # Chiede se vuoi cambiare parametri
    root = Tk(); root.withdraw()
    ans = simpledialog.askstring("Parametri","Modifica parametri? (s/n)")
    root.destroy()
    if ans and ans.lower().startswith('s'):
        panel, entries = crea_pannello_parametri(bin_dict, fit_params, fit_params_limit)
        #ROOT.gApplication.Run()  # attende OK
        # leggi valori
        for k,e in entries.items():
            v = e.GetNumber()
            if k in fit_params: fit_params[k]=v
            elif k in fit_params_limit: fit_params_limit[k]=v
            else:
                dk,sk = k.rsplit('_',1)
                bin_dict[dk][sk]=int(v)

    if foc and path:
        analizza_root(path, bin_dict, fit_params, fit_params_limit, foc, ud, clock)
        ROOT.gApplication.Run()
    else:
        print("Nessuna analisi eseguita.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisi file .root")
    parser.add_argument("--clock", action="store_true", help="Plotta la distribuzione nel tempo dei muoni")
    parser.add_argument("--ud", action="store_true", help="Mostra anche i plot separati per up e dawn")
    args = parser.parse_args()

    ud = args.ud
    clock = args.clock

    ROOT.gROOT.SetBatch(False)
    #if not hasattr(ROOT, 'gApplicROOT.gApplicationation') or not ROOT.gApplication:
    #    app = ROOT.TApplication("app", 0, ctypes.c_void_p())
    #else:
    #    app = ROOT.gApplication

    root_gui(ud, clock)