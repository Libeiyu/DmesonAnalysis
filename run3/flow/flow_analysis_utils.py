'''
Analysis utilities for flow analysis
'''
import ROOT
import sys
import numpy as np

def get_vn_versus_mass(thnSparse, inv_mass_bins, mass_axis, vn_axis, debug=False):
    '''
    Project vn versus mass

    Input:
        - thnSparse:
            THnSparse, input THnSparse obeject (already projected in centrality and pt)
        - inv_mass_bins:
            list of floats, bin edges for the mass axis
        - mass_axis:
            int, axis number for mass
        - vn_axis:
            int, axis number for vn
        - debug:
            bool, if True, create a debug file with the projections (default: False)

    Output:
        - hist_mass_proj:
            TH1D, histogram with vn as a function of mass
    '''
    hist_vn_proj = thnSparse.Projection(vn_axis, mass_axis)
    hist_mass_proj = thnSparse.Projection(mass_axis)
    hist_mass_proj.Reset()
    invmass_bins = np.array(inv_mass_bins)
    hist_mass_proj = ROOT.TH1D('hist_mass_proj', 'hist_mass_proj', len(invmass_bins)-1, invmass_bins)
    
    if debug:
        outfile = ROOT.TFile('debug.root', 'RECREATE')
    
    for i in range(hist_mass_proj.GetNbinsX()):
        bin_low = hist_vn_proj.GetXaxis().FindBin(invmass_bins[i])
        bin_high = hist_vn_proj.GetXaxis().FindBin(invmass_bins[i+1])
        profile = hist_vn_proj.ProfileY(f'profile_{bin_low}_{bin_high}', bin_low, bin_high)
        mean_sp = profile.GetMean()
        mean_sp_err = profile.GetMeanError()
        hist_mass_proj.SetBinContent(i+1, mean_sp)
        hist_mass_proj.SetBinError(i+1, mean_sp_err)
    
    if debug:
        hist_vn_proj.Write()
        hist_mass_proj.Write()
        outfile.Close()
    
    return hist_mass_proj

def get_resolution(resolution_file_name, wagon_id, dets, centMin, centMax, doEP=False):
    '''
    Compute resolution for SP or EP method

    Input:
        - resolution_file_name: 
            str, path to the resolution file
        - wagon_id:
            str, wagon ID
        - dets: 
            list of strings, subsystems to compute the resolution
            if 2 subsystems are given, the resolution is computed as the product of the two
            if 3 subsystems are given, the resolution is computed as the product of the first two divided by the third
        - centMin:
            int, minimum centrality bin
        - centMax:
            int, maximum centrality bin
        - doEP:
            bool, if True, compute EP resolution
            if False, compute SP resolution (default)

    Output:
        - histo_reso:
            TH1D, histogram with the resolution value as a function of centrality
        - histo_dets:
            list of TH1D, list of projections used to compute the resolution
        - histo_means:
            list of TH1D, list of histograms with the mean value of the projections as a function of centrality
    '''
    infile = ROOT.TFile(resolution_file_name, 'READ')
    histo_projs, histo_dets, histo_means = [], [], []
    detA = dets[0]
    detB = dets[1]
    if len(dets) == 3:
        detC = dets[2]
    dets = [f'{detA}{detB}', f'{detA}{detC}', f'{detB}{detC}'] if len(dets) == 3 else [f'{detA}{detB}']
    
    # set path and prefix
    if wagon_id != '':
        wagon_id = f'_id{wagon_id}'
    if doEP:
        path = f'hf-task-flow-charm-hadrons{wagon_id}/epReso/'
        prefix = 'EpReso'
    else:
        path = f'hf-task-flow-charm-hadrons{wagon_id}/spReso/'
        prefix = 'SpReso'
   
    # collect the qvecs and the prepare histo for mean and resolution
    for det in dets:
        histo_dets.append(infile.Get(f'{path}h{prefix}{det}'))
        histo_dets[-1].SetDirectory(0)
        histo_dets[-1].SetName(f'h{prefix}{det}')
        histo_means.append(histo_dets[-1].ProjectionX(f'proj_{histo_dets[-1].GetName()}_mean'))
        histo_means[-1].SetDirectory(0)
        histo_means[-1].Reset()
        histo_projs.append([])

        # collect projections
        for cent in range(centMin, centMax):
            bin_cent_low = histo_dets[-1].GetXaxis().FindBin(cent) # common binning
            bin_cent_high = histo_dets[-1].GetXaxis().FindBin(cent)
            histo_projs[-1].append(histo_dets[-1].ProjectionY(f'proj_{histo_dets[-1].GetName()}_{cent}_{cent}', bin_cent_low, bin_cent_high))
            histo_projs[-1][-1].SetDirectory(0)

        # Appllying absolute value to the projections
        for ihist, _ in enumerate(histo_projs[-1]): histo_means[-1].SetBinContent(ihist+1, histo_projs[-1][ihist].GetMean())
    infile.Close()

    histo_reso = ROOT.TH1F('', '', 100, 0, 100)
    histo_reso.SetDirectory(0)
    for icent in range(centMin, centMax):
        histo_reso.SetBinContent(icent+1, compute_resolution([histo_means[i].GetBinContent(icent+1) for i in range(len(dets))]))

    return histo_reso, histo_dets, histo_means


def compute_resolution(subMean):
    '''
    Compute resolution for SP or EP method

    Input:
        - subMean:
            list of floats, list of mean values of the projections

    Output:
        - resolution:
            float, resolution value
    '''
    if len(subMean) == 1:
        resolution =  subMean[0]
        if resolution <= 0:
            return 0
        else:
            return np.sqrt(resolution)
    elif len(subMean) == 3:
        resolution = (subMean[2] * subMean[1]) / subMean[0] if subMean[0] != 0 else 0
        if resolution <= 0:
            return 0
        else:
            return np.sqrt(resolution)
    else:
        print('ERROR: dets must be a list of 2 or 3 subsystems')
        sys.exit(1)

def get_centrality_bins(centrality):
    '''
    Get centrality bins

    Input:
        - centrality:
            str, centrality class (e.g. 'k3050')

    Output:
        - cent_bins:
            list of floats, centrality bins
        - cent_label:
            str, centrality label
    '''
    if centrality == 'k010':
        return '0_10', [0, 10]
    if centrality == 'k2030':
        return '20_30', [20, 30]
    elif centrality == 'k3040':
        return '30_40', [30, 40]
    elif centrality == 'k3050':
        return '30_50', [30, 50]
    elif centrality == 'k4050':
        return '40_50', [40, 50]
    elif centrality == 'k2060':
        return '20_60', [20, 60]
    elif centrality == 'k4060':
        return '40_60', [40, 60]
    elif centrality == 'k6080':
        return '60_80', [60, 80]
    elif centrality == 'k0100':
        return '0_100', [0, 100]
    else:
        print(f"ERROR: cent class \'{centrality}\' is not supported! Exit")
    sys.exit()

def compute_r2(reso_file, wagon_id, cent_min, cent_max, detA, detB, detC, vn_method):
    '''
    Compute resolution for SP or EP method
    
    Input:
        - reso_file:
            TFile, resolution file
        - wagon_id:
            str, wagon ID
        - cent_min:
            int, minimum centrality bin
        - cent_max:
            int, maximum centrality bin
        - detA:
            str, detector A
        - detB:
            str, detector B
        - detC:
            str, detector C
        - do_ep:
            bool, if True, compute EP resolution
            if False, compute SP resolution

    Output:
        - reso:
            float, resolution value
    '''
    if wagon_id != '':
        wagon_id = f'{wagon_id}'
    if vn_method != 'sp':
        hist_name = f'hf-task-flow-charm-hadrons{wagon_id}/epReso/hEpReso'
    else:
        hist_name = f'hf-task-flow-charm-hadrons{wagon_id}/spReso/hSpReso'

    detA_detB = reso_file.Get(f'{hist_name}{detA}{detB}')
    detA_detC = reso_file.Get(f'{hist_name}{detA}{detC}')
    detB_detC = reso_file.Get(f'{hist_name}{detB}{detC}')

    cent_bin_min = detA_detB.GetXaxis().FindBin(cent_min)
    cent_bin_max = detA_detB.GetXaxis().FindBin(cent_max)

    proj_detA_detB = detA_detB.ProjectionY(f'{hist_name}{detA}{detB}_proj{cent_min}_{cent_max}',
                                           cent_bin_min, cent_bin_max)
    proj_detA_detC = detA_detC.ProjectionY(f'{hist_name}{detA}{detC}_proj{cent_min}_{cent_max}',
                                           cent_bin_min, cent_bin_max)
    proj_detB_detC = detB_detC.ProjectionY(f'{hist_name}{detB}{detC}_proj{cent_min}_{cent_max}',
                                           cent_bin_min, cent_bin_max)

    average_detA_detB = proj_detA_detB.GetMean()
    average_detA_detC = proj_detA_detC.GetMean()
    average_detB_detC = proj_detB_detC.GetMean()

    reso = (average_detA_detB * average_detA_detC) / average_detB_detC if average_detB_detC != 0 else -999
    reso = np.sqrt(reso) if reso > 0 else -999
    return reso

# TODO: extend to vn not only v2
def get_invmass_vs_deltaphi(thnSparse, deltaphiaxis, invmassaxis):
    '''
    Project invariant mass versus deltaphi
    
    Input:
        - thnSparse:
            THnSparse, input THnSparse obeject
        - deltaphiaxis:
            int, axis number for deltaphi
        - invmassaxis:
            int, axis number for invariant mass

    Output:
        - hist_invMass_in:
            TH1D, histogram with invariant mass for in-plane
        - hist_invMass_out:
            TH1D, histogram with invariant mass for out-of-plane
    ''' 
    thn_inplane = thnSparse.Clone('thn_inplane')
    thn_outplane = thnSparse.Clone('thn_outplane')
    hist_cosDeltaPhi_inplane = thn_inplane.Projection(deltaphiaxis, invmassaxis)
    hist_cosDeltaPhi_outplane = thn_outplane.Projection(deltaphiaxis, invmassaxis)
    # In-plane (|cos(deltaphi)| < pi/4)
    hist_cosDeltaPhi_inplane.GetYaxis().SetRangeUser(0, 1)
    hist_invMass_in = hist_cosDeltaPhi_inplane.ProjectionX()
    # Out-of-plane (|cos(deltaphi)| > pi/4)
    hist_cosDeltaPhi_outplane.GetYaxis().SetRangeUser(-1, 0)
    hist_invMass_out = hist_cosDeltaPhi_outplane.ProjectionX()
    hist_invMass_in.SetLineColor(ROOT.kRed)
    del thn_inplane, thn_outplane, hist_cosDeltaPhi_inplane, hist_cosDeltaPhi_outplane
    
    return hist_invMass_in, hist_invMass_out

def get_vnfitter_results(vnFitter, secPeak):
    '''
    Get vn fitter results:
    0: BkgInt
    1: BkgSlope
    2: SgnInt
    3: Mean
    4: Sigma
    5: SecPeakInt
    6: SecPeakMean
    7: SecPeakSigma
    8: ConstVnBkg
    9: SlopeVnBkg
    10: v2Sgn
    11: v2SecPeak

    Input:
        - vnfitter:
            AliHFVnVsMassFitter, vn fitter object
        - secPeak:
            bool, if True, save secondary peak results

    Output:
        - vn_results:
            dict, dictionary with vn results
    '''
    vn_results = {}
    
    vn_results['vn'] = vnFitter.GetVn()
    vn_results['vnUnc'] = vnFitter.GetVnUncertainty()
    vn_results['mean'] = vnFitter.GetMean()
    vn_results['meanUnc'] = vnFitter.GetMeanUncertainty()
    vn_results['sigma'] = vnFitter.GetSigma()
    vn_results['sigmaUnc'] = vnFitter.GetSigmaUncertainty()
    vn_results['ry'] = vnFitter.GetRawYield()
    vn_results['ryUnc'] = vnFitter.GetRawYieldUncertainty()
    vn_results['chi2'] = vnFitter.GetReducedChiSquare()
    vn_results['prob'] = vnFitter.GetFitProbability()
    vn_results['fTotFuncMass'] = vnFitter.GetMassTotFitFunc()
    vn_results['fTotFuncVn'] = vnFitter.GetVnVsMassTotFitFunc()

    if secPeak:
        vn_results['secPeakMeanMass'] = vn_results['fTotFuncMass'].GetParameter(vn_results['fTotFuncMass'].GetParName(6))
        vn_results['secPeakMeanMassUnc'] = vn_results['fTotFuncMass'].GetParError(6)
        vn_results['secPeakSigmaMass'] = vn_results['fTotFuncMass'].GetParameter(vn_results['fTotFuncMass'].GetParName(7))
        vn_results['secPeakSigmaMassUnc'] = vn_results['fTotFuncMass'].GetParError(7)
        vn_results['secPeakMeanVn'] = vn_results['fTotFuncVn'].GetParameter(vn_results['fTotFuncVn'].GetParName(6))
        vn_results['secPeakMeanVnUnc'] = vn_results['fTotFuncVn'].GetParError(6)
        vn_results['secPeakSigmaVn'] = vn_results['fTotFuncVn'].GetParameter(vn_results['fTotFuncVn'].GetParName(7))
        vn_results['secPeakSigmaVnUnc'] = vn_results['fTotFuncVn'].GetParError(7)
        vn_results['vnSecPeak'] = vn_results['fTotFuncVn'].GetParameter(vn_results['fTotFuncVn'].GetParName(11))
        vn_results['vnSecPeakUnc'] = vn_results['fTotFuncVn'].GetParError(11)

    return vn_results

def get_ep_vn(harmonic, nIn, nInUnc, nOut, nOutUnc, resol=1, corr=0):
    '''
    Compute EP vn

    Input:
        - harmonic:
            int, harmonic number
        - nIn:
            float, number of in-plane particles
        - nInUnc:
            float, uncertainty of the number of in-plane particles
        - nOut:
            float, number of out-of-plane particles
        - nOutUnc:
            float, uncertainty of the number of out-of-plane particles
        - resol:
            float, resolution value (default: 1)
        - corr:
            float, correlation between nIn and nOut (default: 1)

    Output:
        - vn:
            float, vn value
        - vnunc:
            float, uncertainty of vn value
    '''
    print(corr)
    if nIn + nOut == 0:
        print('\033[91m ERROR: nIn + nOut = 0. Return 0, 0 \033[0m')
        return 0, 0
    anis = (nIn - nOut) / (nIn + nOut)
    anisDerivIn  = 2 * nOut / ((nIn + nOut)*(nIn + nOut))
    anisDerivOut = -2 * nIn / ((nIn + nOut)*(nIn + nOut))
    anisunc = anisDerivIn * anisDerivIn * nInUnc * nInUnc +\
              anisDerivOut * anisDerivOut * nOutUnc * nOutUnc + \
              2 * anisDerivIn * anisDerivOut * nInUnc * nOutUnc * corr
    if anisunc < 0:
        print('\033[91m ERROR: anisunc < 0. Return 0, 0 \033[0m')
        return 0, 0
    anisunc = np.sqrt(anisunc)

    vn = np.pi / harmonic / harmonic / resol * anis
    vnunc = np.pi / harmonic / harmonic / resol * anisunc

    return vn, vnunc
