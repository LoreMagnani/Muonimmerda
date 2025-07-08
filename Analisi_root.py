import ROOT
import os
import numpy as np
import scipy.signal as sig
import ctypes
from tkinter import filedialog, simpledialog, Tk
from datetime import datetime, timedelta
import argparse
import time

ROOT.gStyle.SetOptFit(1111)

# keepalive con scope globale per evitare GC prematuro
_active_canvases = []
_active_panels   = []

# Funzione di fit esponenziale (se serve altrove)
def d_exp_func(x, par):
    return par[0] * np.exp(-x / par[1]) + par[2] + par[3] * np.exp(-x / par[4])

# Processa un singolo file ROOT e restituisce le differenze
def process_file_diffs(filepath):
    file = ROOT.TFile.Open(filepath)
    tree = file.Get("DigiTree")

    tutti_ev, tutti_up, tutti_dawn = [], [], []
    n_entries = int(tree.GetEntries())
    for i in range(n_entries):
        tree.GetEntry(i)
        event_id = int(tree.EventId)
        ch0 = np.array(tree.Channel0)
        ch1 = np.array(tree.Channel1)
        clock = float(tree.EventTime)

        p0, _ = sig.find_peaks(-ch0, height=-2900, prominence=1000)
        p1, _ = sig.find_peaks(-ch1, height=-2900, prominence=1000)

        if len(p0) == 1 and len(p1) == 1:
            e = [event_id] + p0.tolist() + p1.tolist() + [clock]
            tutti_dawn.append(e)
            tutti_ev.append(e)
        elif len(p0) == 0 and len(p1) == 2:
            e = [event_id] + p1.tolist() + [clock]
            tutti_up.append(e)
            tutti_ev.append(e)

    # Calcola differenze (4*(t1-t0))
    diffs = {
        'all':  [4 * abs(e[2] - e[1]) for e in tutti_ev],
        'up':   [4 * abs(e[2] - e[1]) for e in tutti_up],
        'dawn': [4 * abs(e[2] - e[1]) for e in tutti_dawn],
        'clock': [e[3] for e in tutti_ev]
    }
    return diffs

# Modifica i titoli dei plot in base ai miei nomi (personalizzabile)
def plot_title(nomefile, tipo):
    suffix = {
        "all": "",
        "up": " - eventi up",
        "dawn": " - eventi down"
    }.get(tipo)

    titoli = {
        "Sale_test": "Vita media nel Sale",
        "test_alluminio": "Vita media nell'alluminio",
        "Pasquatot": "Vita media del muone",
        "Pasqua": "Vita media del muone",
        "Invertito_5000": "Vita media con rivelatori invertiti",
        "SolenoideSpento": "Vita media nel solenoide spento",
        "SolenoideAcceso": "Asimmetria con campo magnetico"
    }

    titolo = titoli.get(nomefile)
    if titolo:
        if suffix:
            return titolo + suffix 
        else:
            return titolo
    else:
        return 0

# Normalizza fondo
def normalizza_fondo(dati, fondo, tipo, bins, clock_dati, clock_fondo):
    x_max = max(dati + fondo) * 1.1  # Estendi un po' oltre il massimo

    # Crea istogrammi ROOT
    hist_dati = ROOT.TH1F(f"hist_dati_{tipo}", f"Dati {tipo}", bins, 0, x_max)
    hist_fondo = ROOT.TH1F(f"hist_fondo_{tipo}", f"Fondo {tipo}", bins, 0, x_max)

    for val in dati:
        hist_dati.Fill(val)
    for val in fondo:
        hist_fondo.Fill(val)

    # Calcolo durata di acquisizione
    dt_dati = max(clock_dati) - min(clock_dati)
    dt_fondo = max(clock_fondo) - min(clock_fondo)

    print(dt_dati, dt_fondo)

    # Normalizza il fondo
    scala = dt_dati / dt_fondo if dt_fondo != 0 else 0
    hist_fondo.Scale(scala)

    # Sottrai
    hist_dati.Add(hist_fondo, -1)

    # Tronca bin negativi a 0
    for i in range(1, hist_dati.GetNbinsX() + 1):
        if hist_dati.GetBinContent(i) < 0:
            hist_dati.SetBinContent(i, 0)

    return hist_dati

# Funzione di plotting e fitting con ROOT
def plot_e_fit(diff, tipo, nomefile, bin_dict, fit_params, fit_params_limit, fondo, clock_dati):
    bins      = bin_dict[tipo]['bins']
    start_bin = bin_dict[tipo]['start']
    x_max     = max(diff) * 1.1

    # Istogramma ROOT
    titolo = plot_title(nomefile, tipo)
    print(titolo)
    if titolo:
        hist = ROOT.TH1F(f"hist_{tipo}", titolo, bins, 0, x_max)
    else:
        hist = ROOT.TH1F(f"hist_{tipo}", f"Fit {tipo} - {nomefile}", bins, 0, x_max)
    if fondo:
        accum_fondo = {'all': [], 'up': [], 'dawn': [], 'clock': []}
        files = [os.path.join(fondo, f) for f in os.listdir(fondo) if f.lower().endswith('.root')]
        nomefile = os.path.basename(fondo.rstrip('/\\'))
        for fpath in files:
            print("Elaboro fondo:", fpath)
            diffs_fondo = process_file_diffs(fpath)
            for t in accum_fondo: accum_fondo[t].extend(diffs_fondo[t])

        hist = normalizza_fondo(diff, accum_fondo[tipo], tipo, bins, clock_dati, accum_fondo['clock'])
    else:
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
    fit_5p_NaCl.SetParName(0, "A")
    fit_5p_NaCl.SetParName(1, "#tau_{free}")
    fit_5p_NaCl.SetParName(2, "C")
    fit_5p_NaCl.SetParName(3, "B")
    fit_5p_NaCl.SetParName(4, "#tau_{NaCl}")
    fit_5p_NaCl.SetParameters(fit_params['B'], fit_params['#tau_{free}'], fit_params['A'], fit_params['C'], fit_params['#tau_{NaCl}'])
    fit_5p_NaCl.SetParLimits(4, fit_params_limit['#tau_{NaCl}_inf'], fit_params_limit['#tau_{NaCl}_sup'])
    fit_5p_NaCl.SetParLimits(1, fit_params_limit['#tau_{free}_inf'], fit_params_limit['#tau_{free}_sup'])

    fit_5p_Al = ROOT.TF1(f"fit5_Al_{tipo}", "[0]*exp(-x/[1]) + [2] + [3]*exp(-x/[4])", 0, x_max)
    fit_5p_Al.SetParName(0, "A")
    fit_5p_Al.SetParName(1, "#tau_{free}")
    fit_5p_Al.SetParName(2, "C")
    fit_5p_Al.SetParName(3, "B")
    fit_5p_Al.SetParName(4, "#tau_{Al}")
    fit_5p_Al.SetParameters(fit_params['B'], fit_params['#tau_{free}'], fit_params['A'], fit_params['C'], fit_params['#tau_{Al}'])
    fit_5p_Al.SetParLimits(4, fit_params_limit['#tau_{Al}_inf'], fit_params_limit['#tau_{Al}_sup'])
    fit_5p_Al.SetParLimits(1, fit_params_limit['#tau_{free}_inf'], fit_params_limit['#tau_{free}_sup'])

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

    # Salvataggio
    outdir = "./Fina_na_lfile"
    if not os.path.exists(outdir): os.makedirs(outdir)
    c.SaveAs(f"{outdir}/{nomefile}_{tipo}.pdf")

# Funzione principale: unisce tutti i file se cartella, o singolo
def analizza_root(path, bin_dict, fit_params, fit_params_limit, foc, plot_updown, clock, fondo):
    # Accumulatori globali di diff
    accum = {'all': [], 'up': [], 'dawn': [], 'clock': []}

    if foc == "file":
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
    
    if clock:
        plotClock(accum['clock'], nomefile)

    # Ora un unico plot per ciascun tipo
    for tipo in ['all', 'up', 'dawn']:
        if tipo == 'all' or (plot_updown and tipo in ['up', 'dawn']):
            plot_e_fit(accum[tipo], tipo, nomefile, bin_dict, fit_params, fit_params_limit, fondo, accum['clock'])

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

# Dialogo utente per scegliere il fondo
def file_fondo():
    root = Tk(); root.withdraw()
    s = simpledialog.askstring("Modalità", "Vuoi selezionare un fondo da sottrarre? (s/n)")
    root.destroy()
    if s and s.lower().startswith('s'):
        return filedialog.askdirectory()
    else:
        return None

# Dialogo utente per modificare i parametri prima del fit panel
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

    fondo = file_fondo()

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

def plotClock(clock, nomefile):
    # Converte i clocktime (secondi dal 1960) in datetime
    clock_time = [datetime(1960, 1, 1) + timedelta(seconds=float(sec)) for sec in clock]

    # Converte di nuovo in secondi UNIX (ROOT usa come riferimento il 1 gennaio 1970)
    seconds_from_1970 = [(dt - datetime(1970, 1, 1)).total_seconds() for dt in clock_time]

    # Calcola range temporale e binning orario
    t_min = min(seconds_from_1970)
    t_max = max(seconds_from_1970)
    n_bins = int((t_max - t_min) / 3600) + 1  # 1 bin per ora

    # Istogramma ROOT
    hist = ROOT.TH1F(f"hist_{nomefile}", "",  # titolo vuoto, verrà impostato dopo
                     n_bins, t_min, t_min + n_bins * 3600)
    
    # Riempimento
    for val in seconds_from_1970:
        hist.Fill(val)

    # Calcolo date iniziale e finale per il titolo
    dt_start = min(clock_time)
    dt_end = max(clock_time)
    t_start = dt_start.strftime("%d/%m/%Y %H")
    t_end   = dt_end.strftime("%d/%m/%Y %H")
    title = f"Distribuzioni eventi per ora\n da {t_start} a {t_end}"
    hist.SetTitle(title)

    # Disegna su canvas
    c = ROOT.TCanvas(f"c_{nomefile}", f"Clock histogram", 800, 600)
    hist.GetXaxis().SetTitle("Ora (HH)")
    hist.GetYaxis().SetTitle("Numero di eventi")
    hist.SetFillColorAlpha(ROOT.kBlue-7, 0.35)

    # Mostra solo l'ora sull'asse X
    hist.GetXaxis().SetTimeDisplay(1)
    hist.GetXaxis().SetTimeFormat("%H")
    hist.GetXaxis().SetTimeOffset(0, "gmt")
    hist.GetXaxis().SetNdivisions(n_bins, False)

    hist.Draw("HIST")

    # Salvataggio
    outdir = "./Fina_na_lfile"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    c.SaveAs(f"{outdir}/{nomefile}_clock.pdf")

def tutte_finestre_chiuse():
    for c in _active_canvases:
        if c and not c.IsZombie() and c.GetWindow() != 0:
            return False
    return True

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


    while True:
        root_gui(ud, clock) 

        #app.Run()

        ## LOOP EVENTI NON BLOCCANTE AL POSTO DI app.Run()
        #running = True
        #while running:
        #    ROOT.gSystem.ProcessEvents()
        #    time.sleep(0.01)  # evita CPU 100%
        #    if tutte_finestre_chiuse():
        #        running = False

        for obj in _active_canvases:
            try:
                obj.Close()
                obj.Delete()
            except Exception:
                pass
        _active_canvases.clear()
        _active_panels.clear()

        root = Tk(); root.withdraw()
        from tkinter import messagebox
        answer = messagebox.askyesno("Nuova analisi", "Vuoi analizzare un altro file/cartella?")
        root.destroy()      

        if not answer.lower().startswith('s'):
            print("Uscita dal programma.")
            break