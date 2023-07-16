'''
Script for the computation of the D+ and Ds+ efficiency mesons from ProjectDplusDsSparse.py output
run: python ComputeEfficiencyDplusDs.py fitConfigFileName.yml centClass inputFileNameCent.root inputFileNameFast.root outFileName.root
'''

import argparse
import ctypes
import numpy as np
import pandas as pd
import yaml
import uproot
from ROOT import TFile, TCanvas, TH1F, TLegend  # pylint: disable=import-error,no-name-in-module
from ROOT import gROOT, kRed, kAzure, kFullCircle, kOpenSquare # pylint: disable=import-error,no-name-in-module
from utils.AnalysisUtils import ComputeEfficiency
from utils.StyleFormatter import SetGlobalStyle, SetObjectStyle


parser = argparse.ArgumentParser(description='Arguments')
parser.add_argument('fitConfigFileName', metavar='text', default='config_Ds_Fit.yml')
parser.add_argument('centClass', metavar='text', default='')
parser.add_argument('inFileNameCent', metavar='text', default='')
parser.add_argument('inFileNameFast', metavar='text', default='')
parser.add_argument('outFileName', metavar='text', default='')
parser.add_argument("--batch", help="suppress video output", action="store_true")
args = parser.parse_args()

CentEvents=2.22154e+07
FastEvents=2.06507e+07 
cuts=[1.6,1.2,1.0,1.0]

with open(args.fitConfigFileName, 'r') as ymlfitConfigFile:
    fitConfig = yaml.load(ymlfitConfigFile, yaml.FullLoader)

cent = ''
if args.centClass == 'k010':
    cent = 'Cent010'
elif args.centClass == 'k3050':
    cent = 'Cent3050'
elif args.centClass == 'k6080':
    cent = 'Cent6080'
elif args.centClass == 'kpp5TeVPrompt':
    cent = 'pp5TeVPrompt'
elif args.centClass == 'kpp5TeVFD':
    cent = 'pp5TeVFD'
elif args.centClass == 'kpp13TeVPrompt':
    cent = 'pp13TeVPrompt'
elif args.centClass == 'kpp13TeVFD':
    cent = 'pp13TeVFD'
elif args.centClass == 'kXic0pPb5TeVPrompt':
    cent = 'Xic0pPb5TeVPrompt'
else: 
    print(f'ERROR: centrality {args.centClass} is not supported! Exit')
    exit()

gROOT.SetBatch(args.batch)
SetGlobalStyle(padleftmargin=0.14, padbottommargin=0.12, titlesize=0.045, labelsize=0.04)

ptMins = fitConfig[cent]['PtMin']
ptMaxs = fitConfig[cent]['PtMax']
ptLims = list(ptMins)
nPtBins = len(ptMins)
ptLims.append(ptMaxs[-1])

hEffPrompt = TH1F('hEffPrompt', ';#it{p}_{T} (GeV/#it{c});Efficiency', nPtBins, np.asarray(ptLims, 'd'))
hEffFD = TH1F('hEffFD', ';#it{p}_{T} (GeV/#it{c});Efficiency', nPtBins, np.asarray(ptLims, 'd'))
hYieldPromptGen = TH1F('hYieldPromptGen', ';#it{p}_{T} (GeV/#it{c}); # Generated MC', nPtBins, np.asarray(ptLims, 'd'))
hYieldFDGen = TH1F('hYieldFDGen', ';#it{p}_{T} (GeV/#it{c}); # Generated MC', nPtBins, np.asarray(ptLims, 'd'))
hYieldPromptReco = TH1F('hYieldPromptReco', ';#it{p}_{T} (GeV/#it{c}); # Reco MC', nPtBins, np.asarray(ptLims, 'd'))
hYieldFDReco = TH1F('hYieldFDReco', ';#it{p}_{T} (GeV/#it{c}); # Reco MC', nPtBins, np.asarray(ptLims, 'd'))
SetObjectStyle(hEffPrompt, color=kRed+1, markerstyle=kFullCircle)
SetObjectStyle(hEffFD, color=kAzure+4, markerstyle=kOpenSquare, markersize=1.5, linewidh=2, linestyle=7)
SetObjectStyle(hYieldPromptGen, color=kRed+1, markerstyle=kFullCircle)
SetObjectStyle(hYieldFDGen, color=kAzure+4, markerstyle=kOpenSquare, markersize=1.5, linewidh=2, linestyle=7)
SetObjectStyle(hYieldPromptReco, color=kRed+1, markerstyle=kFullCircle)
SetObjectStyle(hYieldFDReco, color=kAzure+4, markerstyle=kOpenSquare, markersize=1.5, linewidh=2, linestyle=7)

hRecoPromptCent, hRecoFDCent, hGenPromptCent, hGenFDCent,hRecoPromptFast, hRecoFDFast, hGenPromptFast, hGenFDFast = ([] for iHisto in range(8))


for iPt, (ptMin, ptMax) in enumerate(zip(ptMins, ptMaxs)):
    Tree= uproot.open((f'/home/fchinu/Xic0_pPb_5TeV/Cutscan/wSDDnewtrains/Aod224/pt_{ptMin:.0f}-{ptMax:.0f}/cut_{cuts[iPt]}/ml_application/Eff_pT_{ptMin:.0f}_{ptMax:.0f}_ModelApplied.root'))
    dfTest=Tree['treeML'].arrays(library='pd')
    num_test=len(dfTest)
    print(num_test)
    del dfTest
    dfsel=pd.read_parquet(f'/home/fchinu/Xic0_pPb_5TeV/Cutscan/wSDDnewtrains/Data/MC/pt_{ptMin:.0f}-{ptMax:.0f}/cut_{cuts[iPt]}/all_PandaForTraining_pPb_{ptMin:.0f}_{ptMax:.0f}_20220728.parquet.gzip')
    num_sel=len(dfsel)
    print(num_sel)
    del dfsel
    infile = TFile(args.inFileNameCent)
    hRecoPromptCent.append(infile.Get('hPromptPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hRecoFDCent.append(infile.Get('hFDPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hGenPromptCent.append(infile.Get('hPromptGenPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hGenFDCent.append(infile.Get('hFDGenPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))

    # get unweighted yields (for uncertainty)
    nRecoPromptUncCent, nGenPromptUncCent, nRecoFDUncCent, nGenFDUncCent = (ctypes.c_double() for _ in range(4))
    nRecoPromptCent = hRecoPromptCent[iPt].IntegralAndError(0, hRecoPromptCent[iPt].GetNbinsX()+1, nRecoPromptUncCent)
    nGenPromptCent = hGenPromptCent[iPt].IntegralAndError(0, hGenPromptCent[iPt].GetNbinsX()+1, nGenPromptUncCent)
    nRecoFDCent = hRecoFDCent[iPt].IntegralAndError(0, hRecoFDCent[iPt].GetNbinsX()+1, nRecoFDUncCent)
    nGenFDCent = hGenFDCent[iPt].IntegralAndError(0, hGenFDCent[iPt].GetNbinsX()+1, nGenFDUncCent)
    effPromptCent, effPromptUncCent = ComputeEfficiency(nRecoPromptCent, nGenPromptCent, nRecoPromptUncCent.value, nGenPromptUncCent.value)
    effFDCent, effFDUncCent = ComputeEfficiency(nRecoFDCent, nGenFDCent, nRecoFDUncCent.value, nGenFDUncCent.value)
    print(ptMin,ptMax,effPromptCent,effFDCent)
    infile.Close()

    infile = TFile(args.inFileNameFast)
    hRecoPromptFast.append(infile.Get('hPromptPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hRecoFDFast.append(infile.Get('hFDPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hGenPromptFast.append(infile.Get('hPromptGenPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))
    hGenFDFast.append(infile.Get('hFDGenPt_%0.f_%0.f' % (ptMin*10, ptMax*10)))

    # get unweighted yields (for uncertainty)
    nRecoPromptUncFast, nGenPromptUncFast, nRecoFDUncFast, nGenFDUncFast = (ctypes.c_double() for _ in range(4))
    nRecoPromptFast = hRecoPromptFast[iPt].IntegralAndError(0, hRecoPromptFast[iPt].GetNbinsX()+1, nRecoPromptUncFast)
    nGenPromptFast = hGenPromptFast[iPt].IntegralAndError(0, hGenPromptFast[iPt].GetNbinsX()+1, nGenPromptUncFast)
    nRecoFDFast = hRecoFDFast[iPt].IntegralAndError(0, hRecoFDFast[iPt].GetNbinsX()+1, nRecoFDUncFast)
    nGenFDFast = hGenFDFast[iPt].IntegralAndError(0, hGenFDFast[iPt].GetNbinsX()+1, nGenFDUncFast)
    effPromptFast, effPromptUncFast = ComputeEfficiency(nRecoPromptFast, nGenPromptFast, nRecoPromptUncFast.value, nGenPromptUncFast.value)
    effFDFast, effFDUncFast = ComputeEfficiency(nRecoFDFast, nGenFDFast, nRecoFDUncFast.value, nGenFDUncFast.value)
    print(ptMin,ptMax,effPromptFast,effFDFast)
    infile.Close()
    
    effPrompt=(effPromptCent*CentEvents+effPromptFast*FastEvents)/(FastEvents+CentEvents)
    effPromptUnc=(effPromptUncCent*CentEvents+effPromptUncFast*FastEvents)/(FastEvents+CentEvents)
    effFD=(effFDCent*CentEvents+effFDFast*FastEvents)/(FastEvents+CentEvents)
    effFDUnc=(effFDUncCent*CentEvents+effFDUncFast*FastEvents)/(FastEvents+CentEvents)
    print(ptMin,ptMax,effPrompt,effFD)

    nGenPrompt=nGenPromptFast+nGenPromptCent
    nGenPromptUnc=nGenPromptUncFast.value+nGenPromptUncCent.value
    nGenFD=nGenFDFast+nGenFDCent
    nGenFDUnc=nGenFDUncFast.value+nGenFDUncCent.value
    nRecoPrompt=nRecoPromptFast+nRecoPromptCent
    nRecoPromptUnc=nRecoPromptUncFast.value+nRecoPromptUncCent.value
    nRecoFD=nRecoFDFast+nRecoFDCent
    nRecoFDUnc=nRecoFDUncFast.value+nRecoFDUncCent.value

    hEffPrompt.SetBinContent(iPt+1, effPrompt)
    hEffPrompt.SetBinError(iPt+1, effPromptUnc)
    hEffFD.SetBinContent(iPt+1, effFD)
    hEffFD.SetBinError(iPt+1, effFDUnc)

    hYieldPromptGen.SetBinContent(iPt+1, nGenPrompt)
    hYieldPromptGen.SetBinError(iPt+1, nGenPromptUnc)
    hYieldFDGen.SetBinContent(iPt+1, nGenFD)
    hYieldFDGen.SetBinError(iPt+1, nGenFDUnc)
    hYieldPromptReco.SetBinContent(iPt+1, nRecoPrompt)
    hYieldPromptReco.SetBinError(iPt+1, nRecoPromptUnc)
    hYieldFDReco.SetBinContent(iPt+1, nRecoFD)
    hYieldFDReco.SetBinError(iPt+1, nRecoFDUnc)

leg = TLegend(0.6, 0.2, 0.8, 0.4)
leg.SetTextSize(0.045)
leg.SetFillStyle(0)
leg.AddEntry(hEffPrompt, "Prompt", "p")
leg.AddEntry(hEffFD, "Feed-down", "p")

cEff = TCanvas('cEff', '', 800, 800)
cEff.DrawFrame(ptMins[0], 5.e-3, ptMaxs[nPtBins-1], 1.,
               ';#it{p}_{T} (GeV/#it{c});Efficiency;')
cEff.SetLogy()
hEffPrompt.Draw('same')
hEffFD.Draw('same')
leg.Draw()

outFile = TFile(args.outFileName, 'recreate')
hEffPrompt.Scale(num_sel/num_test)
hEffPrompt.Write()
hEffFD.Write()
hYieldPromptGen.Write()
hYieldFDGen.Write()
hYieldPromptReco.Write()
hYieldFDReco.Write()
outFile.Close()

outFileNamePDF = args.outFileName.replace('.root', '.png')
cEff.SaveAs(outFileNamePDF)

if not args.batch:
    input('Press enter to exit')