#include <cstdlib>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cmath>
#include <string>
#include <stack>
#include <vector>
#include <regex>
#include <dirent.h>

// Inclusioni ROOT necessarie
#include "TTree.h"
#include "TPRegexp.h"
#include "TObjString.h"
#include "TObjArray.h"
#include "TGraph.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TApplication.h"
#include "TAxis.h"
#include "TLegend.h"
#include "TMultiGraph.h"
#include "TH1.h"
#include "TFitResult.h"

using namespace std;

// c++ -std=c++17 `root-config --cflags` -o Tree Tree.cpp `root-config --glibs`
int ProcessTree(const string &xmlFileName , const string &xmlFolder , const string &xmlName)
{
    DIR* dir = opendir(xmlFolder.c_str());

    if (dir == nullptr) {
        std::cerr << "Errore nell'apertura della cartella!" << std::endl;
        return 1;
    }

    regex pattern(xmlName + "_\\d+\\.xml" );

    // Crea la cartella solo se non esiste già
    string crea_cartella = "mkdir -p ./rootfile/" + xmlName;
    system(crea_cartella.c_str());
    string OFolder = "./rootfile/" + xmlName;

    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) { 
        string filename = entry->d_name;

        if (filename == "." || filename == "..") 
            continue;
            
        if (regex_match(filename , pattern)) {
            cout << "Trovato " << filename << endl;
        } else continue;

        string fullPath = xmlFolder + "/" + filename;

        // Costruisco il percorso completo del file XML
        fstream file(fullPath.c_str());
        if (!file)
        {
            cout << "ERROR: il file " << fullPath << " non esiste!" << endl;
            continue;
        }

        // Costruisco il nome del file ROOT di output basandosi sul nome del file XML
        string outputFileName = filename;
        outputFileName.replace(outputFileName.size() - 4, 4, ".root");
        string outputPath = OFolder + "/" + outputFileName;

        /*****************************************************************************/
        /*                    CREAZIONE DEL FILE ROOT PER TREE                     */
        /*****************************************************************************/
        TFile* output = TFile::Open(outputPath.c_str(), "recreate");
        TTree* tree = new TTree("DigiTree", "Digi");

        /*****************************************************************************/
        /*                         IMPOSTAZIONE DELLE VARIABILI                      */
        /*****************************************************************************/
        string line;
        int index;
        const int recordlength = 4096;
        // Allocazione degli array per i canali
        int* vector0 = new int[recordlength];
        int* vector1 = new int[recordlength];
        int* vector2 = new int[recordlength];
        int* vector3 = new int[recordlength];
        int clocktime;

        // Creazione dei rami dell'albero
        tree->Branch("EventId", &index);
        tree->Branch("Channel0", vector0, "Channel0[4096]/I");
        tree->Branch("Channel1", vector1, "Channel1[4096]/I");
        tree->Branch("Channel2", vector2, "Channel2[4096]/I");
        tree->Branch("Channel3", vector3, "Channel3[4096]/I");
        tree->Branch("EventTime", &clocktime);

        // Espressioni regolari per analizzare l'XML
        TPRegexp r_event_open("<event id=\"([0-9]+)\".*");
        TPRegexp r_event_close("</event>");
        TPRegexp r_channel_open("^\\s*<trace channel=\"([0-4])\">(.*)");
        TPRegexp r_channel_close("\\s*</trace>");
        TPRegexp r_event_time("clocktime=\"([0-9]+)\"");

        while (getline(file, line))
        {
            if (!r_event_open.MatchB(line))
                continue;

            TObjArray* obj_array = r_event_open.MatchS(line);
            TObjString* obj_string = (TObjString*)obj_array->At(1);
            index = atoi(obj_string->GetString().Data());
            delete obj_array;
            //cout << "Event " << index << endl;

            TObjArray* clock_array = r_event_time.MatchS(line);
            if (clock_array && clock_array->GetEntriesFast() > 1) {
                TObjString* clock_str = (TObjString*)clock_array->At(1);
                clocktime = atoll(clock_str->GetString().Data());
            } else {
                clocktime = 0;
            }
            delete clock_array;

            // Inizializza gli array a zero per ogni evento
            for (int j = 0; j < recordlength; j++) {
                vector0[j] = 0;
                vector1[j] = 0;
                vector2[j] = 0;
                vector3[j] = 0;
            }

            while (getline(file, line))
            {
                if (r_event_close.MatchB(line))
                {
                    tree->Fill();
                    break;
                }

                if (r_channel_open.MatchB(line))
                {
                    TObjArray* obj_charray = r_channel_open.MatchS(line);
                    TObjString* obj_chstring = (TObjString*)obj_charray->At(1);
                    TObjString* obj_valstring = (TObjString*)obj_charray->At(2);

                    int channel = atoi(obj_chstring->GetString().Data());
                    //cout << "Channel " << channel << endl;

                    stringstream sstream(obj_valstring->GetString().Data());
                    int isample = 0;
                    int val = 0;

                    if (channel == 0)
                    {
                        while (sstream >> val)
                        {
                            vector0[isample] = val;
                            isample++;
                        }
                    }
                    else if (channel == 1)
                    {
                        while (sstream >> val)
                        {
                            vector1[isample] = val;
                            isample++;
                        }
                    }
                    else if (channel == 2)
                    {
                        while (sstream >> val)
                        {
                            vector2[isample] = val;
                            isample++;
                        }
                    }
                    else if (channel == 3)
                    {
                        while (sstream >> val)
                        {
                            vector3[isample] = val;
                            isample++;
                        }
                    }
                    // Se necessario, aggiungere elaborazioni per altri canali (2, 3) - aggiunti
                }
            }
        }

        tree->Write();
        output->Close();

        // Liberazione della memoria
        delete[] vector0;
        delete[] vector1;
        delete[] vector2;
        delete[] vector3;
    }
    
    closedir(dir);

    return 0;

}

int main(int argc, char **argv)
{
    if (argc != 3)
    {
        cout << "Utilizzo: " << argv[0] << " nome cartella" << " nome_file senza .xml" << endl;
        return 1;
    }
    string xmlName = argv[2];
    string nomecartella = argv[1];
    string xmlFolder = "xmlfile/" + nomecartella;
	string xmlFileName = xmlFolder + xmlName + ".xml";
    return ProcessTree(xmlFileName , xmlFolder , xmlName);
}