import numpy as np
import ROOT
import matplotlib.pyplot as plt
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from scipy.optimize import curve_fit
from odf import text
import ctypes
import pandas as pd

def trova_dati(file_path, start_row, end_row, column_index, page_name):
    """
    Legge i dati da un foglio Excel e restituisce soglie, counts, il nome del rivelatore e il voltaggio.
    
    Args:
        file_path (str): Il percorso del file Excel.
        start_row (int): La riga di partenza per i dati (1-based, come nell'Excel visivo).
        end_row (int): La riga di fine per i dati (1-based, come nell'Excel visivo).
        column_index (int): L'indice della colonna (1-based, come nell'Excel visivo).
        sheet_name (str): Il nome del foglio di lavoro da cui leggere i dati.
    
    Returns:
        tuple: Una tupla contenente:
            - soglie (pandas.Series): I valori della colonna A tra le righe specificate.
            - counts (pandas.Series): I valori della colonna specificata tra le righe specificate.
            - nome_rivelatore (str): Il nome del rivelatore trovato 3 righe sopra la riga di partenza.
            - voltaggio (str): Il voltaggio trovato 2 righe sopra la riga di partenza.
    """
    # Leggi il foglio specificato
    df = pd.read_excel(file_path, sheet_name=page_name, header=None)
    
    # Conversione da 1-based Excel a 0-based Python
    start_idx = start_row - 1
    end_idx = end_row - 1
    col_idx = column_index - 1
    
    # Estrai il nome del rivelatore e il voltaggio
    nome_rivelatore = df.iloc[start_idx - 3, col_idx]
    voltaggio = df.iloc[start_idx - 2, col_idx]
    
    # Estrai le soglie (colonna A) e i counts (colonna specificata)
    soglie = pd.to_numeric(df.iloc[start_idx:end_idx + 1, 0], errors='coerce')
    counts = pd.to_numeric(df.iloc[start_idx:end_idx + 1, col_idx], errors='coerce')
    
    # Restituisci i dati richiesti
    return soglie, counts, nome_rivelatore, voltaggio

def trova_dati_per_il_coglione_con_linux(file_name, start_row, end_row, column_index, page_name):
    """
    Legge i dati da un file .ods e restituisce soglie, counts, il nome del rivelatore e il voltaggio.
    
    Args:
        file_name (str): Il nome del file .ods (deve essere nella stessa directory del codice).
        start_row (int): La riga di partenza per i dati (1-based, come nell'Excel visivo).
        end_row (int): La riga di fine per i dati (1-based, come nell'Excel visivo).
        column_index (int): L'indice della colonna (1-based, come nell'Excel visivo).
        sheet_name (str): Il nome del foglio di lavoro da cui leggere i dati.
    
    Returns:
        tuple: Una tupla contenente:
            - soglie (pandas.Series): I valori della colonna A tra le righe specificate.
            - counts (pandas.Series): I valori della colonna specificata tra le righe specificate.
            - nome_rivelatore (str): Il nome del rivelatore trovato 3 righe sopra la riga di partenza.
            - voltaggio (str): Il voltaggio trovato 2 righe sopra la riga di partenza.
    """
    # Leggi il foglio specificato
    df = pd.read_excel(file_name, engine='odf', sheet_name=page_name, header=None)
    
    # Conversione da 1-based Excel a 0-based Python
    start_idx = start_row - 1
    end_idx = end_row - 1
    col_idx = column_index - 1
    
    # Estrai il nome del rivelatore e il voltaggio
    nome_rivelatore = df.iloc[start_idx - 3, col_idx]
    voltaggio = f"{df.iloc[start_idx - 2, col_idx]} + V"
    
    # Estrai le soglie (colonna A) e i counts (colonna specificata)
    soglie = pd.to_numeric(df.iloc[start_idx:end_idx + 1, 0], errors='coerce')
    counts = pd.to_numeric(df.iloc[start_idx:end_idx + 1, col_idx], errors='coerce')
    
    # Restituisci i dati richiesti
    return soglie, counts, nome_rivelatore, voltaggio

def solo_plot(soglie, counts, nome_rivelatore, volt):
    # Creazione della figura con matplotlib
    plt.figure(figsize=(10, 6))

    # Plot dei punti originali usando soglie come coordinate x
    plt.plot(counts, soglie, 'o', label='Punti Originali', color='black')

    # Etichette e titolo
    if volt is not None:
        plt.title(f"Plot di {nome_rivelatore} a {volt}V")
    else:
        plt.title(f"Plot di {nome_rivelatore} a (voltaggio non trovato)")
    plt.xlabel("Soglia")
    plt.ylabel("Conteggi")

    # Aggiungere la legenda
    plt.legend()

    # Salvataggio del grafico come immagine
    output_filename = f"Plot_{nome_rivelatore}_{volt}V.pdf"
    plt.tight_layout()
    plt.savefig(output_filename, format='pdf')
    plt.close()
    print(f"Grafico salvato come immagine: {output_filename}")

def fit_plateau(soglie, counts, nome_rivelatore, volt, lungo):
    if len(counts) < lungo:
        raise ValueError("Non ci sono abbastanza dati validi per trovare un plateau.")

    # Assicura che soglie sia convertibile in numerico
    try:
        x_coords = np.array([float(label) for label in soglie])  # Usa soglie come x
    except ValueError:
        raise ValueError("Le coordinate X (soglie) devono essere numeriche.")

    # Variabili per memorizzare il miglior plateau
    best_chi_squared = float("inf")
    best_start = 0
    best_end = 0

    # Scansiona tutti gli intervalli possibili
    for start in range(len(counts)):
        for end in range(start + lungo, len(counts)):
            window = np.array(counts[start:end + 1])
            x_data = x_coords[start:end + 1]

            try:
                # Fit con una costante
                popt, _ = curve_fit(a_fit, x_data, window)
                a_fit = popt[0]
                residuals = window - a_fit
                chi_squared = np.sum((residuals) ** 2) / len(residuals)

                # Se il chi-quadro è migliore, aggiorna i parametri
                if chi_squared < best_chi_squared:
                    best_chi_squared = chi_squared
                    best_start = start
                    best_end = end
            except RuntimeError:
                continue  # Se il fit fallisce, passa al prossimo intervallo

    # Dati del plateau trovato
    plateau_x = x_coords[best_start:best_end + 1]
    plateau_y = counts[best_start:best_end + 1]

    # Debug: mostra plateau
    print("Plateau X:", plateau_x)
    print("Plateau Y:", plateau_y)

    # Creazione del canvas ROOT
    canvas = ROOT.TCanvas(f"canvas_col_{volt}", f"Fit Plateau a {volt}", 800, 600)

    # Crea il grafico con tutti i punti
    all_graph = ROOT.TGraph(len(x_coords), 
                            (ctypes.c_double * len(x_coords))(*x_coords), 
                            (ctypes.c_double * len(counts))(*counts))
    all_graph.SetTitle(f"Fit {nome_rivelatore} a {volt}V")
    all_graph.GetXaxis().SetTitle("soglie")
    all_graph.GetYaxis().SetTitle("Counts")
    all_graph.SetMarkerStyle(20)
    all_graph.SetMarkerColor(ROOT.kBlack)

    # Crea il grafico solo per il plateau
    plateau_graph = ROOT.TGraph(len(plateau_x), 
                                (ctypes.c_double * len(plateau_x))(*plateau_x), 
                                (ctypes.c_double * len(plateau_y))(*plateau_y))
    plateau_graph.SetMarkerStyle(20)
    plateau_graph.SetMarkerColor(ROOT.kBlue)

    # Aggiunge testi accanto ai punti
    for i, (x, y) in enumerate(zip(x_coords, counts)):
        label_text = ROOT.TLatex(x, y, f"{x:.2f}")  # Mostra valore X
        label_text.SetTextSize(0.02)
        label_text.SetTextAlign(22)  # Centrato
        label_text.Draw()

    # Definizione della funzione costante (retta orizzontale)
    fit_function = ROOT.TF1("constante", "[0]", min(plateau_x), max(plateau_x))
    fit_function.SetParameter(0, np.mean(plateau_y))

    # Fit del grafico plateau
    plateau_graph.Fit(fit_function, "Q")

    # Estrai i parametri del fit
    costante = fit_function.GetParameter(0)
    print(f"Valore della costante (fit): {costante}")

    # Aggiungi una legenda con i parametri del fit
    legend = ROOT.TLegend(0.7, 0.8, 0.9, 0.9)  # Posizione: (x1, y1, x2, y2)
    legend.SetHeader("Fit Plateau", "C")  # Titolo della legenda
    legend.AddEntry(all_graph, "Dati", "P")  # Grafico completo
    legend.AddEntry(plateau_graph, f"Plateau", "P")  # Plateau
    legend.AddEntry(fit_function, f"Costante: {costante:.2f}", "L")  # Fit costante
    legend.SetTextSize(0.03)  # Dimensione del testo
    legend.Draw()  # Disegna la legenda sul canvas

    # Disegna tutto sul canvas
    all_graph.Draw("AP")  # Punti neri
    plateau_graph.Draw("P SAME")  # Plateau blu
    fit_function.SetLineColor(ROOT.kRed)
    fit_function.Draw("SAME")  # Linea rossa del fit
    legend.Draw()  # La legenda deve essere ridisegnata

    # Forza l'aggiornamento del canvas
    canvas.Update()

    # Salvataggio del grafico come PDF
    output_filename = f"Plateau_{nome_rivelatore}_a_{volt}.pdf"
    canvas.SaveAs(output_filename)  # Salva il grafico
    print(f"Grafico salvato come PDF: {output_filename}")

    # Chiude il canvas per evitare conflitti
    canvas.Close()

def unicum(num_graphs, file_path, start_row, end_row, page_name):
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.tab10  # Tavolozza di colori con 10 colori predefiniti
    
    for i in range(num_graphs):
        soglie, counts, nome_rivelatore, volts = trova_dati_per_il_coglione_con_linux(file_path, start_row, end_row, i, page_name)

        # Colore unico per ogni ciclo
        color = colors(i % 10)
        
        # Usa labels numerici per l'asse X e values per l'asse Y
        ax.scatter(soglie, counts, label=f'{volts} Volts', color=color, alpha=0.8)

    # Configurazione del grafico
    ax.set_title(f"Grafico per '{nome_rivelatore}'")
    ax.set_xlabel("Asse X")
    ax.set_ylabel("Asse Y")
    
    # Inclinare le etichette sull'asse X di 45 gradi
    plt.xticks(rotation=45)

    # Mostrare la legenda
    ax.legend()  # Mostra legenda per distinguere i set di dati
    
    # Salva il grafico come PDF
    output_filename = f"Unico_{nome_rivelatore}.pdf"
    plt.savefig(output_filename, format='pdf')
    print(f"Grafico salvato come: {output_filename}")

    # Chiude il grafico per liberare memoria
    plt.close(fig)


