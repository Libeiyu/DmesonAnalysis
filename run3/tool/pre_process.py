'''
This sricpt is used to pre-process a/multi large AnRes.root for the BDT training:
    - split the input by pT
    - obtain the sigma from prompt enhance sample
python3 pre_process.py config_pre.yml AnRes_1.root AnRes_2.root --pre --sigma  
'''
import os
import sys
import yaml
import numpy as np
import array
import ROOT
from ROOT import TFile
import argparse
import itertools
from concurrent.futures import ProcessPoolExecutor
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{script_dir}/../flow/")
sys.path.append(f"{script_dir}/../flow/BDT")
from flow_analysis_utils import get_centrality_bins
from sparse_dicts import get_sparses
# from proj_thn_mc import pt_weights_info, proj_mc_reco, proj_mc_gen

class PreselectedData:
    preselected = False # if the data is preselected, ussing preselected = True

def multi_Proj(sparse, iSparse, centmin, centmax, outputDir):
    # sparse, iSparse, centmin, centmax, outputDir, suffix = proj_args
    out_file = TFile(f'{outputDir}/pre/AnRes/Projections_{centmin}_{centmax}_{iSparse}.root', 'recreate')
    for idim in range(sparse.GetNdimensions()):
        histo = sparse.Projection(idim)
        histo.SetName(sparse.GetAxis(idim).GetName())
        histo.SetTitle(sparse.GetAxis(idim).GetTitle())
        histo.Write()
    out_file.Close()
    
def merge_files(outputDir, centmin, centmax, nFiles):
    out_file = TFile(f'{outputDir}/pre/AnRes/Projections_{centmin}_{centmax}.root', 'recreate')
    for iSparse in range(nFiles):
        in_file = TFile(f'{outputDir}/pre/AnRes/Projections_{centmin}_{centmax}_{iSparse}.root')
        out_file.mkdir(f'Flow_{iSparse}')
        out_file.cd(f'Flow_{iSparse}')
        for key in in_file.GetListOfKeys():
            obj = key.ReadObj()
            obj.Write()
        in_file.Close()
    out_file.Close()
    
def process_pt_bins(iPt, ptmin, ptmax, config, sparse_axes, thnsparse_list, axestokeep, outputDir):
    # iPt, ptmin, ptmax, centmin, centmax, config, sparse_axes, thnsparse_list, axestokeep, outputDir, suffix = pt_args
    print(f'Processing pT bins {ptmin} - {ptmax}')
    
    processed_sparse = None
    for iSparse, (_, sparse) in enumerate(thnsparse_list.items()):
        
        if PreselectedData.preselected:
            if iPt != iSparse:
                print(f"Skipping sparse {iSparse} for pT bin {iPt}")
                continue
        
        cloned_sparse = sparse.Clone(f"{sparse.GetName()}_clone_{iPt}_{iSparse}")
        cloned_sparse.GetAxis(sparse_axes['Flow']['Pt']).SetRangeUser(ptmin, ptmax)

        if config.get('bkg_cuts'):
            bkg_cut = config['bkg_cuts'][iPt]
            if bkg_cut != -1:
                cloned_sparse.GetAxis(sparse_axes['Flow']['score_bkg']).SetRangeUser(0, bkg_cut)

        axes_to_project = array.array('i', [sparse_axes['Flow'][axtokeep] for axtokeep in axestokeep])
        thn_proj = cloned_sparse.Projection(len(axestokeep), axes_to_project, 'O')
        thn_proj.SetName(f"{cloned_sparse.GetName()}_{iPt}")
        
        cloned_sparse.Delete()
        del cloned_sparse

        # if config.get('RebinSparse'):
        #     rebin_factors = array.array('i', [config['RebinSparse'][axtokeep] for axtokeep in axestokeep])
        #     if -1 not in rebin_factors:
        #         processed_sparse = processed_sparse.Rebin(len(rebin_factors), rebin_factors)
        
        if PreselectedData.preselected:
            processed_sparse = thn_proj.Clone()    
        else:
            if iSparse == 0:
                processed_sparse = thn_proj.Clone()
            else:
                processed_sparse.Add(thn_proj)
        thn_proj.Delete()
        del thn_proj

    outFile = TFile(f'{outputDir}/pre/AnRes/AnalysisResults_pt_{int(ptmin*10)}_{int(ptmax*10)}.root', 'recreate')
    outFile.mkdir('hf-task-flow-charm-hadrons')
    outFile.cd('hf-task-flow-charm-hadrons')
    processed_sparse.Write('hSparseFlowCharm')
    outFile.Close()
    processed_sparse.Delete()
    del processed_sparse
    
    ROOT.gDirectory.Close()
    ROOT.gROOT.GetListOfFiles().Delete()

    print(f'Finished processing pT bin {ptmin} - {ptmax}')

def pre_process(config, ptmins, ptmaxs, centmin, centmax, axestokeep, outputDir):
    # mkdir for the output
    os.makedirs(f'{outputDir}/pre/AnRes', exist_ok=True)
    
    # Load the ThnSparse
    thnsparse_list, _, _, sparse_axes = get_sparses(config, True, False, False, anres_files=config['flow_files'])

    for _, sparse in thnsparse_list.items():
        sparse.GetAxis(sparse_axes['Flow']['cent']).SetRangeUser(centmin, centmax)

    # projection
    task_proj_args = [(sparse, iSparse, centmin, centmax, outputDir) for iSparse, (sparse_key, sparse) in enumerate(thnsparse_list.items())]
    with ProcessPoolExecutor() as executor:
        proj = executor.map(multi_Proj, *zip(*task_proj_args))
        for result in proj:
            result
    merge_files(outputDir, centmin, centmax, len(thnsparse_list))

    # pre-process with pT bins
    pt_args = [(iPt, ptmin, ptmax, config, sparse_axes, thnsparse_list, axestokeep, outputDir) for iPt, (ptmin, ptmax) in enumerate(zip(ptmins, ptmaxs))]
    with ProcessPoolExecutor(5) as executor:
        pt_process = executor.map(process_pt_bins, *zip(*pt_args))
        for result in pt_process:
            result
        
def get_sigma(preFiles, config_pre, centrality, resolution, outputDir, skip_projection=False):
    with open(config_pre, 'r') as cfgPre:
        config = yaml.safe_load(cfgPre)

    apply_btd_cuts = config['apply_btd_cuts']    
    
    if not apply_btd_cuts:
        print("Warning: 'apply_btd_cuts' is not enabled in the config_pre.")
    
    if not skip_projection:
        skip_proj = ''
    else:
        skip_proj = '--skip_projection'
    
    os.makedirs(f'{outputDir}/pre/sigma', exist_ok=True)

    str_preFiles = ' '.join(preFiles)
    command = (f"python3 ../flow/run_full_flow_analysis.py {config_pre} {str_preFiles} \
                -c {centrality} -o {outputDir}/pre/sigma \
                -s sigma -v sp --r {resolution} \
                --skip_efficiency --skip_resolution \
                {skip_proj}")
    os.system(f'{command}')

def process_pt_bin_Singlecut(iPt, ptmin, ptmax, centMin, centMax, config, bkg_max_cuts, sig_mins, sig_maxs, thnsparse_list, sparse_axes, axestokeep, outputDir):

    print(f'Processing pT bin {ptmin} - {ptmax}, cent {centMin}-{centMax}')

    # add possibility to apply cuts for different variables
    processed_sparses = []
    for iThn, (sparse_key, sparse) in enumerate(thnsparse_list.items()):
        cloned_sparse = sparse.Clone()
        cloned_sparse.GetAxis(sparse_axes['Flow']['Pt']).SetRangeUser(ptmin, ptmax)
        cloned_sparse.GetAxis(sparse_axes['Flow']['cent']).SetRangeUser(centMin, centMax)
        
        temp_thn_projs = []
        for iSig, (sig_min, sig_max) in enumerate(zip(sig_mins, sig_maxs)):
            temp_cloned_sparse = cloned_sparse.Clone()
            temp_cloned_sparse.GetAxis(sparse_axes['Flow']['score_bkg']).SetRangeUser(0, bkg_max_cuts[iSig])
            temp_cloned_sparse.GetAxis(sparse_axes['Flow']['score_FD']).SetRangeUser(sig_min, sig_max)
            temp_thn_projs.append(temp_cloned_sparse.Projection(len(axestokeep), array.array('i', [sparse_axes['Flow'][axtokeep] for axtokeep in axestokeep]), 'O'))
            temp_thn_projs[-1].SetName(cloned_sparse.GetName() + f'_sig_{iSig}')
            temp_cloned_sparse.Delete()
            del temp_cloned_sparse
            
        # delete the cloned sparse
        cloned_sparse.Delete()
        del cloned_sparse
        
        if iThn == 0:
            for iSig, thn_proj in enumerate(temp_thn_projs):
                processed_sparse = thn_proj.Clone()
                processed_sparses.append(processed_sparse)
                temp_thn_projs[iSig].Delete()
        else:
            for iSig, thn_proj in enumerate(temp_thn_projs):
                processed_sparses[iSig].Add(thn_proj)
                temp_thn_projs[iSig].Delete()

        del temp_thn_projs
    
        if config.get('RebinSparse'):
            rebin_factors = array.array('i', [config['RebinSparse'][axtokeep] for axtokeep in axestokeep])
            if -1 not in rebin_factors:
                processed_sparse = processed_sparse.Rebin(len(rebin_factors), rebin_factors)

    for iSig, processed_sparse in enumerate(processed_sparses):
        outFile = ROOT.TFile(f'{outputDir}/pre_sys/AnRes/{iSig:02d}/AnalysisResults_pt_{int(ptmin*10)}_{int(ptmax*10)}.root', 'recreate')
        outFile.mkdir('hf-task-flow-charm-hadrons')
        outFile.cd('hf-task-flow-charm-hadrons')
        processed_sparse.Write('hSparseFlowCharm')
        outFile.Close()
        processed_sparses[iSig].Delete()
    del processed_sparse

def pre_sys_process(config, ptmins, ptmaxs, centmin, centmax, axestokeep, outputDir):
    
    os.makedirs(f'{outputDir}/pre_sys/AnRes', exist_ok=True)
    
    # Load the ThnSparse
    thnsparse_list, _, _, sparse_axes = get_sparses(config, True, False, False, config['flow_files'])

    bkg_cuts = config['bdt_cut']['bkg_cuts']
    sig_mins = config['bdt_cut']['sig_mins']
    sig_maxs = config['bdt_cut']['sig_maxs']

    mCutset = max(len(sig_min) for sig_min in sig_mins)
    for iCut in range(mCutset):
        os.makedirs(f'{outputDir}/pre_sys/AnRes/{iCut:02d}', exist_ok=True)

    # Loop over each pt bin in parallel
    max_workers = 12 # hyperparameter
    args = [(iPt, ptmin, ptmax, centmin, centmax, config, bkg_cuts[iPt], sig_mins[iPt], sig_maxs[iPt], thnsparse_list, sparse_axes, axestokeep, outputDir) for iPt, (ptmin, ptmax) in enumerate(zip(ptmins, ptmaxs))]
    with ProcessPoolExecutor(max_workers=4) as executor:
        tasks = executor.map(process_pt_bin_Singlecut, *zip(*args))
        for result in tasks:
            result

    for iPt in range(len(ptmins)):
        if len(sig_mins[iPt]) < mCutset:
            available_file_index = len(sig_mins[iPt])
            for iCut in range(available_file_index, mCutset):
                os.system(f'cp -r {outputDir}/pre_sys/AnRes/{(available_file_index-1):02d}/AnalysisResults_pt_{int(ptmins[iPt]*10)}_{int(ptmaxs[iPt]*10)}.root {outputDir}/pre_sys/AnRes/{iCut:02d}/')
    # with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
    #     tasks = [executor.submit(process_pt_bin_Singlecut, iPt, ptmin, ptmax, centmin, centmax, bkg_maxs[iPt], sig_mins[iPt], sig_maxs[iPt], thnsparse_list, sparse_axes, axestokeep, outputDir) for iPt, (ptmin, ptmax) in enumerate(zip(ptmins, ptmaxs))]
    #     for task in concurrent.futures.as_completed(tasks):
    #         task.result()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument('config_pre', metavar='text', 
                        default='config_pre.yml', help='configuration file')
    parser.add_argument('--out_dir', metavar='text', default="", 
                        help='output directory for projected .root files')
    parser.add_argument('--pre', action='store_true', help='pre-process the AnRes.root')
    parser.add_argument('--sigma', action='store_true', help='get the sigma')
    parser.add_argument('--pre_sys', action='store_true', help='pre-process the AnRes.root for systematic')
    parser.add_argument('--skip_projection', '-sp', action='store_true', help='skip the projection')
    parser.add_argument("--suffix", "-s", metavar="text", default="", help="suffix for output files")
    args = parser.parse_args()

    if not args.pre and not args.sigma and not args.pre_sys:
        print('Please specify the action to perform.')
        sys.exit(1)

    with open(args.config_pre, 'r') as cfgPre:
        config = yaml.safe_load(cfgPre)
  
    # Load the configuration
    ptmins = config['ptmins']
    ptmaxs = config['ptmaxs']
    axestokeep = config['axestokeep']
    outputDir = args.out_dir if args.out_dir != "" else config['skim_out_dir'] 
    
    centMin, centMax = get_centrality_bins(config['centrality'])[1]
    
    if args.pre:
        pre_process(config, ptmins, ptmaxs, centMin, centMax, axestokeep, outputDir)
        os.system(f'cp {args.config_pre} {outputDir}/pre/AnRes')
    
    if args.sigma:
        
        centrality = config['centrality']
        resolution = config['resolution']
        
        if os.path.exists(f'{outputDir}/pre'):
            preFiles = [f'{outputDir}/pre/AnRes/AnalysisResults_pt{iFile}.root' for iFile in range(len(ptmins))]
        else:
            raise ValueError(f'No eff folder found in {outputDir}')
        preFiles.sort()
        
        # you have to know the sigma from the differet prompt enhance samples is stable first
        get_sigma(preFiles, args.config_pre, centrality, resolution, outputDir, skip_projection=args.skip_projection)
        
    if args.pre_sys:
        pre_sys_process(config, ptmins, ptmaxs, centMin, centMax, axestokeep, outputDir)
        os.system(f'cp {args.config_pre} {outputDir}/pre_sys/AnRes')