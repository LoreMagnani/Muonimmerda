import numpy as np
import ROOT
import matplotlib.pyplot as plt
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from scipy.optimize import curve_fit
from odf import text
import ctypes

# Funzione per leggere i dati dal file .ods 
def read_ods_page(file_path, page_name):
    doc = load(file_path)
    table = None
    for sheet in doc.getElementsByType(Table):
        if sheet.getAttribute("name") == page_name:
            table = sheet
            break
    
    if table is None:
        raise ValueError(f"Foglio '{page_name}' non trovato nel file .ods")
    
    data = []
    for row in table.getElementsByType(TableRow):
        cells = row.getElementsByType(TableCell)
        row_data = []
        for cell in cells:
            cell_text = ""
            for paragraph in cell.getElementsByType(text.P):
                if paragraph.firstChild is not None and hasattr(paragraph.firstChild, 'data'):
                    cell_text += paragraph.firstChild.data
            row_data.append(cell_text.strip())
        if row_data:
            data.append(row_data)
    
    return data

# Trova il valore sopra "counts"
def find_volt(data, start_row, column):
    for row in range(start_row, -1, -1):  # Scendi all'indietro dalla riga specificata
        if data[row][column] == "Counts":  # Cerca "Counts" nella colonna specificata
            return data[row - 1][column]  # Restituisci il valore della cella sopra
        else:
            if row == 1:
                return None  # Restituisci None se non trovi "counts"

# Funzione per fit y=cost
def constant_fit(x, a):
    return a  # Funzione costante per il plateau

# Funzione base per disegnare il plot (Counts per soglie fissato voltaggio)
def save_graph(file_path, page_name, bottom_row, top_row, output_filename_prefix, i):   
    data = read_ods_page(file_path, page_name)

    values = []
    labels = []
    el = 0

    for j in range(bottom_row, top_row + 1):
        if j < len(data) and data[j]:
            label = data[j][0]
            cell_value = data[j][i]

            if '/' in cell_value:
                el += 1  # Salta i valori nulli
                continue

            # Aggiungi il valore numerico al grafico
            labels.append(float(label) if label else 0)  # Converti label in float se possibile
            values.append(float(cell_value) if cell_value else 0)

    # Creazione della figura con matplotlib
    plt.figure(figsize=(10, 6))

    # Plot dei punti originali usando labels come coordinate x
    plt.plot(labels, values, 'o', label='Punti Originali', color='black')

    # Etichette e titolo
    volt = find_volt(data, bottom_row , i)  # Cerca a partire da bottom_row
    if volt is not None:
        plt.title(f"Plot di {page_name} a {volt}V")
    else:
        plt.title(f"Plot di {page_name} a (voltaggio non trovato)")
    plt.xlabel("Soglia")
    plt.ylabel("Conteggi")

    # Aggiungere la legenda
    plt.legend()

    # Salvataggio del grafico come immagine
    if volt is not None:
        output_filename = f"{output_filename_prefix}_plot_{page_name}_{volt}V.pdf"
    else:
        output_filename = f"{output_filename_prefix}_{page_name}_colonna_{chr(64 + i + 1)}.pdf"
    plt.tight_layout()
    plt.savefig(output_filename, format='pdf')
    plt.close()
    print(f"Grafico salvato come immagine: {output_filename}")

# Cerca plateau nel plot e fitta con retta y=cost (Counts per soglie fissato voltaggio)
def find_plateau(file_path, page_name, bottom_row, top_row, column, min_plateau_length):
    # Legge i dati e li prepara
    data = read_ods_page(file_path, page_name)

    # Estrae valori e labels
    values = []
    labels = []
    for j in range(bottom_row, top_row + 1):
        cell_value = data[j][column] if len(data[j]) > column else ""
        if "/" in cell_value or not cell_value.strip():
            continue  # Salta i valori non validi
        try:
            values.append(float(cell_value))
            labels.append(data[j][0] if len(data[j]) > 0 else "")
        except ValueError:
            continue  # Ignora valori non numerici

    if len(values) < min_plateau_length:
        raise ValueError("Non ci sono abbastanza dati validi per trovare un plateau.")

    # Assicura che labels sia convertibile in numerico
    try:
        x_coords = np.array([float(label) for label in labels])  # Usa labels come x
    except ValueError:
        raise ValueError("Le coordinate X (labels) devono essere numeriche.")

    # Variabili per memorizzare il miglior plateau
    best_chi_squared = float("inf")
    best_start = 0
    best_end = 0

    # Scansiona tutti gli intervalli possibili
    for start in range(len(values)):
        for end in range(start + min_plateau_length, len(values)):
            window = np.array(values[start:end + 1])
            x_data = x_coords[start:end + 1]

            try:
                # Fit con una costante
                popt, _ = curve_fit(constant_fit, x_data, window)
                a_fit = popt[0]
                residuals = window - constant_fit(x_data, a_fit)
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
    plateau_y = values[best_start:best_end + 1]

    # Debug: mostra plateau
    print("Plateau X:", plateau_x)
    print("Plateau Y:", plateau_y)

    # Creazione del canvas ROOT
    canvas = ROOT.TCanvas(f"canvas_col_{column}", f"Fit Plateau Colonna {column}", 800, 600)

    volt = find_volt(data, bottom_row, column)

    # Crea il grafico con tutti i punti
    all_graph = ROOT.TGraph(len(x_coords), 
                            (ctypes.c_double * len(x_coords))(*x_coords), 
                            (ctypes.c_double * len(values))(*values))
    all_graph.SetTitle(f"Fit {page_name} a {volt}V")
    all_graph.GetXaxis().SetTitle("Labels")
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
    for i, (x, y) in enumerate(zip(x_coords, values)):
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
    output_filename = f"Plateau_{page_name}_col_{column}.pdf"
    canvas.SaveAs(output_filename)  # Salva il grafico
    print(f"Grafico salvato come PDF: {output_filename}")

    # Chiude il canvas per evitare conflitti
    canvas.Close()

# Solo per pagina "CPA": applica find plateau alla tensione migliore (Counts per soglie fissato voltaggio)
def CPA(file_path, page_name, bottom_row, top_row, column, min_plateau_length):
    # Legge i dati e li prepara
    data = read_ods_page(file_path, page_name)

    # Estrae valori e labels
    values = []
    labels = []
    for j in range(bottom_row, top_row + 1):
        cell_value = data[j][column] if len(data[j]) > column else ""
        if "/" in cell_value or not cell_value.strip():
            continue  # Salta i valori non validi
        try:
            values.append(float(cell_value))
            labels.append(data[j][0] if len(data[j]) > 0 else "")
        except ValueError:
            continue  # Ignora valori non numerici

    if len(values) < min_plateau_length:
        raise ValueError("Non ci sono abbastanza dati validi per trovare un plateau.")

    # Assicura che labels sia convertibile in numerico
    try:
        x_coords = np.array([float(label) for label in labels])  # Usa labels come x
    except ValueError:
        raise ValueError("Le coordinate X (labels) devono essere numeriche.")

    # Variabili per memorizzare il miglior plateau
    best_chi_squared = float("inf")
    best_start = 0
    best_end = 0

    # Scansiona tutti gli intervalli possibili
    for start in range(len(values)):
        for end in range(start + min_plateau_length, len(values)):
            window = np.array(values[start:end + 1])
            x_data = x_coords[start:end + 1]

            try:
                # Fit con una costante
                popt, _ = curve_fit(constant_fit, x_data, window)
                a_fit = popt[0]
                residuals = window - constant_fit(x_data, a_fit)
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
    plateau_y = values[best_start:best_end + 1]

    # Debug: mostra plateau
    print("Plateau X:", plateau_x)
    print("Plateau Y:", plateau_y)

    # Trova nome del rivelatore
    if column == 1:
        riv = "Circe"
    elif column == 2:
        riv = "Partenope"
    else:
        riv = "Atena"
    
    volt = find_volt(data, bottom_row, column)

    # Creazione del canvas ROOT
    canvas = ROOT.TCanvas(f"canvas_col_{column}", f"Fit Plateau Colonna {column}", 800, 600)

    volt = find_volt(data, bottom_row, column)

    # Crea il grafico con tutti i punti
    all_graph = ROOT.TGraph(len(x_coords), 
                            (ctypes.c_double * len(x_coords))(*x_coords), 
                            (ctypes.c_double * len(values))(*values))
    all_graph.SetTitle(f"Fit {riv} a {volt}V")
    all_graph.GetXaxis().SetTitle("Labels")
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
    for i, (x, y) in enumerate(zip(x_coords, values)):
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
    output_filename = f"{riv}_a_{volt}.pdf"
    canvas.SaveAs(output_filename)  # Salva il grafico
    print(f"Grafico salvato come PDF: {output_filename}")

    # Chiude il canvas per evitare conflitti
    canvas.Close()

# Per mettere a confronto diverse tensioni dello stesso riv nello stesso grafico 
def unicum(file_path, page_name, bottom_row, top_row, output_filename_prefix, num_graphs):
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.tab10  # Tavolozza di colori con 10 colori predefiniti
    
    for i in range(num_graphs):
        # Legge i dati e li prepara
        data = read_ods_page(file_path, page_name)

        # Estrae valori e labels per ciascun grafico
        values = []
        labels = []
        print(f"Processing graph {i+1}")

        for j in range(bottom_row, top_row + 1):
            cell_value = data[j][i+1] if len(data[j]) > i+1 else ""
            if "/" in cell_value or not cell_value.strip():
                continue  # Salta i valori non validi
            try:
                values.append(float(cell_value))
                labels.append(float(data[j][0]) if len(data[j]) > 0 else "")
            except ValueError:
                continue  # Ignora valori non numerici

        ## Debug: Verifica i dati letti e accumulati per ogni ciclo
        #print(f"Labels ({len(labels)}): {labels}")
        #print(f"Values ({len(values)}): {values}")
        
        # Ottieni il valore di volts (usando la funzione finds_volts)
        volts = find_volt(data, bottom_row, i+1)

        # Colore unico per ogni ciclo
        color = colors(i % 10)
        
        # Usa labels numerici per l'asse X e values per l'asse Y
        ax.scatter(labels, values, label=f'{volts} Volts', color=color, alpha=0.8)

    # Configurazione del grafico
    ax.set_title(f"Grafico per '{page_name}'")
    ax.set_xlabel("Asse X")
    ax.set_ylabel("Asse Y")
    
    # Inclinare le etichette sull'asse X di 45 gradi
    plt.xticks(rotation=45)

    # Mostrare la legenda
    ax.legend()  # Mostra legenda per distinguere i set di dati
    
    # Salva il grafico come PDF
    output_filename = f"{output_filename_prefix}_unico_{page_name}.pdf"
    plt.savefig(output_filename, format='pdf')
    print(f"Grafico salvato come: {output_filename}")

    # Chiude il grafico per liberare memoria
    plt.close(fig)

