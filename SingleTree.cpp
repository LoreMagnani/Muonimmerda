#include <cstdlib>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cmath>
#include <string>
#include <stack>
#include <vector>

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

int ProcessTree(const string &xmlFileName)
{
    // Costruisco il percorso completo del file XML
    string xmlFilePath = "./xmlfile/" + xmlFileName;
    fstream file(xmlFilePath.c_str());
    if (!file)
    {
        cout << "ERROR: il file " << xmlFileName << " non esiste!" << endl;
        return 0;
    }


    // Costruisco il nome del file ROOT di output basandosi sul nome del file XML
    string outputFileName = xmlFileName;
    if (outputFileName.size() >= 4 && outputFileName.substr(outputFileName.size()-4) == ".xml")
    {
        outputFileName.replace(outputFileName.size()-4, 4, ".root");
    }
    else
    {
        outputFileName += ".root";
    }
    string outputFilePath = "./rootfile/" + outputFileName;

    /*****************************************************************************/
    /*                    CREAZIONE DEL FILE ROOT PER TREE                     */
    /*****************************************************************************/
    TFile* output = TFile::Open(outputFilePath.c_str(), "recreate");
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

    // Creazione dei rami dell'albero
    tree->Branch("EventId", &index);
    tree->Branch("Channel0", vector0, "Channel0[4096]/I");
    tree->Branch("Channel1", vector1, "Channel1[4096]/I");
    tree->Branch("Channel2", vector2, "Channel2[4096]/I");
    tree->Branch("Channel3", vector3, "Channel3[4096]/I");

    // Espressioni regolari per analizzare l'XML
    TPRegexp r_event_open("<event id=\"([0-9]+)\".*");
    TPRegexp r_event_close("</event>");
    TPRegexp r_channel_open("^\\s*<trace channel=\"([0-4])\">(.*)");
    TPRegexp r_channel_close("\\s*</trace>");

    while (getline(file, line))
    {
        if (!r_event_open.MatchB(line))
            continue;

        TObjArray* obj_array = r_event_open.MatchS(line);
        TObjString* obj_string = (TObjString*)obj_array->At(1);
        index = atoi(obj_string->GetString().Data());
        cout << "Event " << index << endl;

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
                cout << "Channel " << channel << endl;

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
                // Se necessario, aggiungere elaborazioni per altri canali (2, 3)
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

    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2)
    {
        cout << "Utilizzo: " << argv[0] << " nome_file.xml" << endl;
        return 1;
    }
    string xmlName = argv[1];
	string xmlFileName = xmlName + ".xml";
    return ProcessTree(xmlFileName);
}
