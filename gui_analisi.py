import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import uproot
import numpy as np
import scipy.optimize as opt
import scipy.signal as sig
import matplotlib.pyplot as plt
import os
import csv

# === Funzioni di analisi ===
def exp_func(x, a, tau, b):
    return a * np.exp(-x / tau) + b

def analizza_file(filepath, bin_dict, fit_params, plot_updown, save_csv=False, csv_writer=None, uno=False):
    
    if uno:
        nomefile = os.path.splitext(os.path.basename(filepath))[0]
        file = uproot.open(filepath)
        tree = file["DigiTree"]

        event_id = tree["EventId"].array()
        ch0 = tree["Channel0"].array()
        ch1 = tree["Channel1"].array()

        tutti_ev, tutti_up, tutti_dawn = [], [], []
        for i in range(len(event_id)):
            p0, _ = sig.find_peaks(-ch0[i], height=-2900, prominence=1000)
            p1, _ = sig.find_peaks(-ch1[i], height=-2900, prominence=1000)

            if len(p0) == 1 and len(p1) == 1:
                e = [event_id[i]] + p0.tolist() + p1.tolist()
                tutti_dawn.append(e)
                tutti_ev.append(e)
            elif len(p0) == 0 and len(p1) == 2:
                e = [event_id[i]] + p1.tolist()
                tutti_up.append(e)
                tutti_ev.append(e)
    else:
        tutti_ev, tutti_up, tutti_dawn = [], [], []
        nomefile = os.path.splitext(os.path.basename(filepath))[0]
        #print(nomefile)
        for fname in os.listdir(filepath):
            if fname.endswith(".root"):
                fpath = os.path.join(filepath, fname)
                file = uproot.open(fpath)
                tree = file["DigiTree"]

                event_id = tree["EventId"].array()
                ch0 = tree["Channel0"].array()
                ch1 = tree["Channel1"].array()

                for i in range(len(event_id)):
                    p0, _ = sig.find_peaks(-ch0[i], height=-2900, prominence=1000)
                    p1, _ = sig.find_peaks(-ch1[i], height=-2900, prominence=1000)

                    if len(p0) == 1 and len(p1) == 1:
                        e = [event_id[i]] + p0.tolist() + p1.tolist()
                        tutti_dawn.append(e)
                        tutti_ev.append(e)
                    elif len(p0) == 0 and len(p1) == 2:
                        e = [event_id[i]] + p1.tolist()
                        tutti_up.append(e)
                        tutti_ev.append(e)       

    def build_diff(evlist):
        return [4 * abs(e[2] - e[1]) for e in evlist]

    diff_all = build_diff(tutti_ev)
    diff_up = build_diff(tutti_up)
    diff_dawn = build_diff(tutti_dawn)

    if not os.path.exists("./Fina_na_lfile"):
        os.makedirs("./Fina_na_lfile")

    def plot_fit(diff, tipo):
        bin_count = bin_dict[tipo]['bins']
        start_bin = bin_dict[tipo]['start']

        counts, bin_edges = np.histogram(diff, bins=bin_count)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        x_fit = bin_centers[start_bin:]
        y_fit = counts[start_bin:]

        if fit_params['auto']:
            p0 = (max(y_fit), 2000, 5)
        else:
            p0 = (fit_params['a'], fit_params['tau'], fit_params['b'])

        try:
            popt, pcov = opt.curve_fit(exp_func, x_fit, y_fit, p0=p0, sigma=np.sqrt(np.maximum(y_fit, 1)))
            perr = np.sqrt(np.diag(pcov))
        except Exception as e:
            messagebox.showerror("Errore nel fit", str(e))
            return

        a, tau, b = popt
        sigma_a, sigma_tau, sigma_b = perr

        if save_csv and csv_writer:
            csv_writer.writerow([nomefile, tipo, a, tau, b, sigma_a, sigma_tau, sigma_b])

        plt.figure(figsize=(10, 6))
        plt.hist(diff, bins=bin_count, alpha=0.7, color='blue', edgecolor='black', label="Dati")
        plt.plot(bin_centers, exp_func(bin_centers, *popt), 'r--',
                 label=f"Fit: a·exp(-x/τ) + b\nτ = {tau:.2f} ns, a = {a:.2f}, b = {b:.2f}")
        plt.xlabel("Tempo [ns]")
        plt.ylabel("Counts")
        plt.title(f"Fit esponenziale - {tipo}")
        plt.legend()
        plt.grid(True)

        output_path = f"./Fina_na_lfile/{nomefile}_{tipo}.pdf"
        plt.savefig(output_path)
        plt.show()
        plt.close()

    plot_fit(diff_all, "all")
    if plot_updown:
        plot_fit(diff_up, "up")
        plot_fit(diff_dawn, "dawn")

# === GUI ===
def avvia_gui():
    root = tk.Tk()
    root.title("Analisi ROOT GUI")
    root.geometry("500x700")

    file_path = tk.StringVar()
    folder_path = tk.StringVar()
    ud_check = tk.BooleanVar()
    auto_fit = tk.BooleanVar(value=True)
    save_csv = tk.BooleanVar()

    bins_all = tk.IntVar(value=100)
    start_all = tk.IntVar(value=5)
    bins_up = tk.IntVar(value=100)
    start_up = tk.IntVar(value=5)
    bins_dawn = tk.IntVar(value=100)
    start_dawn = tk.IntVar(value=5)

    a_fit = tk.DoubleVar(value=100)
    tau_fit = tk.DoubleVar(value=2000)
    b_fit = tk.DoubleVar(value=5)

    def browse_file():
        filename = filedialog.askopenfilename(filetypes=[("ROOT files", "*.root")])
        if filename:
            file_path.set(filename)

    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            folder_path.set(folder)

    def esegui():
        bin_dict = {
            "all": {'bins': bins_all.get(), 'start': start_all.get()},
            "up": {'bins': bins_up.get(), 'start': start_up.get()},
            "dawn": {'bins': bins_dawn.get(), 'start': start_dawn.get()}
        }

        fit_params = {
            'auto': auto_fit.get(),
            'a': a_fit.get(),
            'tau': tau_fit.get(),
            'b': b_fit.get()
        }

        batch_mode = folder_path.get() != ""
        csv_file = None
        csv_writer = None

        if save_csv.get():
            csv_file = open("./Fina_na_lfile/fit_results.csv", "w", newline="")
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["filename", "fit_type", "a", "tau", "b", "sigma_a", "sigma_tau", "sigma_b"])

        if batch_mode:
            analizza_file(folder_path.get(), bin_dict, fit_params, ud_check.get(), save_csv.get(), csv_writer)           
            #for fname in os.listdir(folder_path.get()):
            #    if fname.endswith(".root"):
            #        fpath = os.path.join(folder_path.get(), fname)
            #        analizza_file(fpath, bin_dict, fit_params, ud_check.get(), save_csv.get(), csv_writer)
        elif file_path.get():
            analizza_file(file_path.get(), bin_dict, fit_params, ud_check.get(), save_csv.get(), csv_writer , uno=True)
        else:
            messagebox.showerror("Errore", "Seleziona un file o una cartella")

        if csv_file:
            csv_file.close()

    # --- Layout ---
    ttk.Label(root, text="Seleziona il file ROOT o la cartella").pack(pady=5)
    ttk.Entry(root, textvariable=file_path, width=50).pack()
    ttk.Button(root, text="Sfoglia file", command=browse_file).pack(pady=2)
    ttk.Entry(root, textvariable=folder_path, width=50).pack()
    ttk.Button(root, text="Sfoglia cartella", command=browse_folder).pack(pady=2)

    ttk.Checkbutton(root, text="Mostra anche up/down", variable=ud_check).pack()
    ttk.Checkbutton(root, text="Salva CSV parametri fit", variable=save_csv).pack()

    # Binning
    frame_bins = ttk.LabelFrame(root, text="Impostazioni binning")
    frame_bins.pack(pady=10, fill="x", padx=10)
    for tipo, var1, var2 in [("all", bins_all, start_all), ("up", bins_up, start_up), ("dawn", bins_dawn, start_dawn)]:
        ttk.Label(frame_bins, text=f"{tipo}: bin - start").pack()
        ttk.Entry(frame_bins, textvariable=var1, width=10).pack()
        ttk.Entry(frame_bins, textvariable=var2, width=10).pack()

    # Fit params
    ttk.Checkbutton(root, text="Fit automatico", variable=auto_fit).pack(pady=5)
    frame_fit = ttk.LabelFrame(root, text="Parametri fit manuale")
    frame_fit.pack(pady=10, fill="x", padx=10)
    for lbl, var in [("a", a_fit), ("tau", tau_fit), ("b", b_fit)]:
        ttk.Label(frame_fit, text=f"{lbl}:").pack()
        ttk.Entry(frame_fit, textvariable=var, width=15).pack()

    ttk.Button(root, text="Esegui Analisi", command=esegui).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    avvia_gui()