# Esegue plot di dati su serie di file .root creati da Tree.cpp
# Sia le cartelle che i singoli file di questo tipo devono essere contenuti in ./rootfile

import uproot
import numpy as np 
import os
import sys
import argparse
import awkward as ak
import scipy as sp
import scipy.optimize as opt
import scipy.signal as sig
import matplotlib.pyplot as plt

def exp_func(x, a, tau, b):
    return a * np.exp(-x / tau) + b

def apri_root_file(nome):
    #file_path = os.path.expanduser(f"./rootfile/{nome}.root")
    file_path = nome
    try:
        file = uproot.open(file_path)
        print(f"✅ File '{nome}' aperto con successo!")
        return file
    except FileNotFoundError:
        print(f"❌ Errore: Il file '{nome}' non esiste in {file_path}.")
        sys.exit(1)

def isto_e_fit(diff, nome_file, uno, cartella, tipo="all"):
    try:
        bin_count = int(input(f"[{tipo}] Numero bin? "))
        start_bin = int(input(f"[{tipo}] Bin iniziale? "))
    except ValueError:
        print("❌ Inserisci numeri interi validi.")
        return

    counts, bin_edges = np.histogram(diff, bins=bin_count)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    x_fit = bin_centers[start_bin:]
    y_fit = counts[start_bin:]

    param = input(f"[{tipo}] Vuoi modificare i parametri del fit? [default: max(yfit), 2000, 5] s/n ").lower()
    if param == 's':
        try:
            p0a = float(input("Valore di a? "))
            p0tau = float(input("Valore di tau? "))
            p0b = float(input("Valore di b? "))
        except ValueError:
            print("❌ Inserisci valori numerici validi.")
            return
    else:
        p0a = max(y_fit)
        p0tau = 2000
        p0b = 5

    try:
        popt, pcov = opt.curve_fit(exp_func, x_fit, y_fit, p0=(p0a, p0tau, p0b), sigma=np.sqrt(np.maximum(y_fit, 1)))
    except RuntimeError:
        print("❌ Fit non riuscito.")
        return

    a_fit, tau_fit, b_fit = popt
    print(f"📈 Parametri fit ({tipo}): a = {a_fit:.2f}, tau = {tau_fit:.2f}, b = {b_fit:.2f}")
    print("📊 Errori sul fit:", np.sqrt(np.diag(pcov)))

    # Plot
    plt.figure(figsize=(10, 6))
    plt.hist(diff, bins=bin_count, alpha=0.7, color='b', edgecolor='black', label='Dati')
    label_fit = f'Fit: a·exp(-x/τ) + b\nτ = {tau_fit:.2f} ns\na = {a_fit:.2f}, b = {b_fit:.2f}'
    plt.plot(bin_centers, exp_func(bin_centers, *popt), 'r--', label=label_fit)
    plt.xlabel("Tempo [ns]")
    plt.ylabel("Counts")
    plt.title(f"Istogramma ({tipo}) con fit esponenziale")
    plt.legend()
    plt.grid(True)

    output_dir = "./Fina_na_lfile"
    os.makedirs(output_dir, exist_ok=True)

    if uno:
        namefile1 = os.path.splitext(nome_file)[0]
        print(namefile1)
        namefile = os.path.split(namefile1)[1]
        output_file = os.path.join(output_dir, f"{namefile}_{tipo}.pdf")
        plt.savefig(output_file)
        plt.show()
        print(f"✅ Istogramma ({tipo}) salvato in: {output_file}")
    else:
        output_file = os.path.join(output_dir, f"{cartella}_{tipo}.pdf")
        plt.savefig(output_file)
        plt.show()
        print(f"✅ Istogramma ({tipo}) salvato in: {output_file}")  

def main():
    parser = argparse.ArgumentParser(description="Analisi file .root")
    parser.add_argument("cartella", type=str, help="Nome della cartella in rootfile con i file ROOT desiderati")
    parser.add_argument("--nomefile", type=str, default="", help="Analizza solo il file ROOT nella cartella rootfile con questo nome (senza estensione)")
    parser.add_argument("--ud", action="store_true", help="Mostra anche i plot separati per up e dawn")
    args = parser.parse_args()

    cartella = os.path.expanduser(f"./rootfile/{args.cartella}/")
    filename = os.path.expanduser(f"./rootfile/{args.nomefile}.root")

    uno = False

    #print(cartella)
    #print(filename)

    file_list = []
    if filename != "./rootfile/.root":
        file_list.append(filename)
        uno = True
    else:
        for fname in os.listdir(cartella):
                    if fname.endswith(".root"):
                        fpath = os.path.join(cartella, fname)
                        file_list.append(fpath)

    #print(file_list)

    tutti_ev = []
    tutti_up = []
    tutti_dawn = []
    ev_up = 0
    ev_dawn = 0

    for nome_file in file_list:
        file = apri_root_file(nome_file)
        #file = nome_file
        tree = file["DigiTree"]

        event_id = tree["EventId"].array()
        channel0 = tree["Channel0"].array()
        channel1 = tree["Channel1"].array()
        channel2 = tree["Channel2"].array()
        channel3 = tree["Channel3"].array()

        ev_up_file = 0
        ev_dawn_file = 0

        for i in range(len(event_id)):
            peaks0, props0 = sig.find_peaks(-channel0[i], height=-2900, prominence=1000)
            peaks1, props1 = sig.find_peaks(-channel1[i], height=-2900, prominence=1000)

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

        print(f"\n📊 Eventi UP in {file}  = {ev_up_file}")
        print(f"📉 Eventi DAWN in {file} = {ev_dawn_file}\n")

    print(f"Eventi UP totali: {ev_up}")
    print(f"Eventi DAWN totali {ev_dawn}")

    diff = [4 * abs(e[2] - e[1]) for e in tutti_ev]
    diff_up = [4 * abs(e[2] - e[1]) for e in tutti_up]
    diff_dawn = [4 * abs(e[2] - e[1]) for e in tutti_dawn]

    # Plot principale
    isto_e_fit(diff, nome_file, uno, args.cartella, tipo="all")

    # Se richiesto, plot separati
    if args.ud:
        print("\n📈 Grafici separati per eventi UP e DAWN:")
        isto_e_fit(diff_up, nome_file, uno, args.cartella, tipo="up")
        isto_e_fit(diff_dawn, nome_file, uno, args.cartella, tipo="dawn")

if __name__ == "__main__":
    main()



