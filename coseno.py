import Analisi_root
import Analisi_root_loro
import ROOT
import os
import ctypes
from tkinter import Tk

ROOT.gStyle.SetOptFit(1111)

# keepalive con scope globale per evitare GC prematuro
_active_canvases = []
_active_panels   = []

# Funzione di plotting e fitting con ROOT
def cos_plot(diff, nomefile, bin_dict, fit_params, fit_params_limit):
    bins = bin_dict
    x_max_up = max(diff["up"]) * 1.1
    x_max_down = max(diff["dawn"]) * 1.1
    x_max = max(x_max_down, x_max_up)

    # Istogramma ROOT
    titolo = Analisi_root.plot_title(nomefile, "all") #"all" serve a non generare quella parte di titolo
    print(titolo)

    # Metto dif in istogrammi diversi 
    h_up = ROOT.TH1F(f"hist_Campo_Magnetico_up", f"{titolo}_up", bins, 0, x_max_up)
    h_down = hist = ROOT.TH1F(f"hist_Campo_Magnetico_down", f"{titolo}_down", bins, 0, x_max_down)
    for val in diff["dawn"]:
        h_down.Fill(val)
    for val in diff["up"]:
        h_up.Fill(val)
    
    # straggo la l'arrey che descrive la distribuzione degli eventi nei bin e calcolo i bin di histo
    if titolo:
        hist = ROOT.TH1F(f"hist_Campo_Magnetico", titolo, bins, 0, x_max)
    else:
        hist = ROOT.TH1F(f"hist_Campo_Magnetico", f"Fit Campo Magnetico - {nomefile}", bins, 0, x_max)

    for i in range(1, bins+1):
        bin_up = h_up.GetBinContent(i)
        bin_down = h_down.GetBinContent(i)
        denom = bin_up + bin_down
        if denom != 0:
            norm = (bin_up - bin_down) / denom
        else:
            norm = 0
        hist.SetBinContent(i, norm)

    # Definizione delle funzioni di fit
    fit_cos = ROOT.TF1(f"cos", "([0]/6)*cos(x*[1]) + [2]", 0, x_max)
    fit_cos.SetParName(0, "#xi")
    fit_cos.SetParName(1, "#omega")
    fit_cos.SetParName(2, "b")
    fit_cos.SetParameters(fit_params['#xi'], fit_params['#omega'], fit_params['b'])
    fit_cos.SetParLimits(1, fit_params_limit['#omega_inf'], fit_params_limit['#omega_sup'])

    # Disegna su canvas
    c = ROOT.TCanvas("c_coseno", "Fit Campo Magnetico", 800, 600)
    hist.GetXaxis().SetTitle("Tempo [ns]")
    hist.GetYaxis().SetTitle("Counts")
    hist.SetFillColorAlpha(ROOT.kBlue-7, 0.35)
    hist.Draw("HIST")

    # Panel interattivo senza fit automatico
    panel = hist.FitPanel()

    # Memorizzazione globale
    _active_canvases.extend([c, hist, fit_cos])
    _active_panels.append(panel)

    # Aggiorna il canvas
    c.Update()

    # Salvataggio
    outdir = "./Fina_na_lfile"
    if not os.path.exists(outdir): os.makedirs(outdir)
    c.SaveAs(f"{outdir}/{nomefile}_coseno.pdf")

# Funzione principale: unisce tutti i file se cartella, o singolo
def cos_analizza_root(path, bin_dict, fit_params, fit_params_limit, foc):
    # Accumulatori globali di diff
    accum = {'all': [], 'up': [], 'dawn': []}

    if foc == "file":
        diffs = Analisi_root_loro.process_file_diffs(path)
        nomefile = os.path.splitext(os.path.basename(path))[0]
        for t in accum: accum[t].extend(diffs[t])
    elif foc == "cartella":
        files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.root')]
        nomefile = os.path.basename(path.rstrip('/\\'))
        for fpath in files:
            print("Elaboro:", fpath)
            diffs = Analisi_root_loro.process_file_diffs(fpath)
            for t in accum: accum[t].extend(diffs[t])
    else:
        print("Modalità non riconosciuta.")
        return

    # Ora un unico plot per ciascun tipo
    cos_plot(accum, nomefile, bin_dict, fit_params, fit_params_limit)

# GUI ROOT con TApplication
def cos_root_gui():
    # Scelta file o cartella
    foc, path = Analisi_root.scegli_f_o_c()
    if not foc or not path:
        print("Nessuna analisi eseguita.")
        return

    # Parametri preimpostati
    bin_dict = 50
    fit_params = {'auto':True, 'b':0.14,"#omega":2.6, "#xi":0.05}
    fit_params_limit = {'auto':True, '#omega_sup':0, '#omega_inf':5}

    if foc and path:
        cos_analizza_root(path, bin_dict, fit_params, fit_params_limit, foc)
        app.Run()
    else:
        print("Nessuna analisi eseguita.")

if __name__ == "__main__":
    # Chiama il gui
    ROOT.gROOT.SetBatch(False)
    if not hasattr(ROOT, 'gApplication') or not ROOT.gApplication:
        app = ROOT.TApplication("app", 0, ctypes.c_void_p())
    else:
        app = ROOT.gApplication


    while True:
        cos_root_gui() 

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