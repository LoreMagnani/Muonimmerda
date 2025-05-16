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
def exp_func(x, par):
    return par[0] * np.exp(-x / par[1]) + par[2]

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

# Funzione di plotting e fitting con ROOT
def plot_e_fit(diff, tipo, nomefile, bin_dict, fit_params):
    bins      = bin_dict[tipo]['bins']
    start_bin = bin_dict[tipo]['start']
    x_max     = max(diff) * 1.1

    # Istogramma ROOT
    hist = ROOT.TH1F(f"hist_{tipo}", f"Fit {tipo} - {nomefile}", bins, 0, x_max)
    for val in diff:
        hist.Fill(val)

    # Definisci funzione di fit
    fit_func = ROOT.TF1(f"fit_{tipo}", "[0]*exp(-x/[1])+[2]", 0, x_max)
    if fit_params['auto']:
        fit_func.SetParameters(hist.GetMaximum(), fit_params['tau'], fit_params['b'])
    else:
        fit_func.SetParameters(fit_params['a'], fit_params['tau'], fit_params['b'])

    # Fitting dal bin di start
    fit_start = hist.GetBinLowEdge(start_bin)
    fit_func.SetRange(fit_start, x_max)
    hist.Fit(fit_func, "RL")

    # Disegna su canvas
    c = ROOT.TCanvas(f"c_{tipo}", f"Fit {tipo}", 800, 600)
    hist.GetXaxis().SetTitle("Tempo [ns]")
    hist.GetYaxis().SetTitle("Counts")
    hist.SetFillColorAlpha(ROOT.kBlue-7, 0.35)
    hist.Draw("HIST")
    fit_func.SetLineColor(ROOT.kRed)
    fit_func.Draw("SAME")

    # 1) Memorizzo in una struttura globale
    _active_canvases.append(c)
    _active_canvases.append(hist)
    _active_canvases.append(fit_func)


    # 2) Apro il pannello interattivo e lo salvo anch’esso
    panel = hist.FitPanel()  
    _active_panels.append(panel)

    # 3) Aggiorno il canvas
    c.Update()

    # Parametri e legenda
    a, tau, b     = fit_func.GetParameter(0), fit_func.GetParameter(1), fit_func.GetParameter(2)
    sigma_a       = fit_func.GetParError(0)
    sigma_tau     = fit_func.GetParError(1)
    sigma_b       = fit_func.GetParError(2)
    legend = ROOT.TLegend(0.55, 0.62, 0.88, 0.88)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry(fit_func, f"#tau = {tau:.2f} #pm {sigma_tau:.2f} ns\n"
                                  f"a = {a:.2f} #pm {sigma_a:.2f}\n"
                                  f"b = {b:.2f} #pm {sigma_b:.2f}", "l")
    legend.Draw()

    # Salvataggio
    outdir = "./Fina_na_lfile"
    if not os.path.exists(outdir): os.makedirs(outdir)
    c.SaveAs(f"{outdir}/{nomefile}_{tipo}.pdf")

# Funzione principale: unisce tutti i file se cartella, o singolo
def analizza_root(path, bin_dict, fit_params, foc, plot_updown, clock):
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
            plot_e_fit(accum[tipo], tipo, nomefile, bin_dict, fit_params)

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

# GUI ROOT con TApplication
def root_gui(ud, clock):
    ROOT.gROOT.SetBatch(False)
    app = ROOT.TApplication("app", 0, ctypes.c_void_p())

    bin_dict = {"all":{'bins':100,'start':5}, "up":{'bins':100,'start':5}, "dawn":{'bins':100,'start':5}}
    fit_params = {'auto':True, 'a':100, 'tau':2000, 'b':5}

    foc, path = scegli_f_o_c()
    if foc and path:
        analizza_root(path, bin_dict, fit_params, foc, ud, clock)
        app.Run()
    else:
        print("Nessuna analisi eseguita.")
    
    app.Run()

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisi file .root")
    parser.add_argument("--clock", action="store_true", help="Plotta la distribuzione nel tempo dei muoni")
    parser.add_argument("--ud", action="store_true", help="Mostra anche i plot separati per up e dawn")
    args = parser.parse_args()

    ud = args.ud
    clock = args.clock

    root_gui(ud, clock)
