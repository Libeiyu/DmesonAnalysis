import os
import sys
import argparse
import ROOT
from ROOT import TFile
import yaml
sys.path.append('/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow')
from flow_analysis_utils import get_resolution, get_centrality_bins, getListOfHisots
sys.path.append('/home/wuct/ALICE/local/reso/DmesonAnalysis')
from utils.StyleFormatter import SetObjectStyle, SetGlobalStyle
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
SetGlobalStyle(padleftmargin=0.15, padbottommargin=0.15,
               padrightmargin=0.15, titleoffsety=1.1, maxdigits=3, titlesizex=0.03,
               labelsizey=0.04, setoptstat=0, setopttitle=0, palette=ROOT.kGreyScale)

centrality = 'k3050'
cent_bins, _ = get_centrality_bins(centrality)
detA = 'FT0c'
detB = 'FV0a'
detC = 'TPCtot'

axes_dict = {
    'cent': 0,
    'FT0cFV0a': 1,
    'FT0cTPCtot': 2,
    'FV0aTPCtot': 3,
    'occu': 4,
    'sel1': 5, # noSameBunchPileup
    'sel2': 6, #  occupancy
    'sel3': 7, #  timerangenarrow
    'sel4': 8, #  timerangestandard
    'sel5': 9, #  rofstandard
    'all': 10
}

occupancy_cut = [[1,1],[2,3],[4,14],[1,14]]

def get_reso_sparses(reso_files, axis, cuts):


    thn_resos = []
    with ThreadPoolExecutor(20) as executor:
        futures = []
        for reso_file in reso_files:
            futures.append(executor.submit(TFile.Open, reso_file, 'read'))
            print(f'Loading {reso_file}')
        
        for iFuture, future in enumerate(futures):
            reso = future.result()
            thn_resos.append(reso.Get('hf-task-flow-charm-hadrons/spReso/hSparseReso'))
            reso.Close()
            print(f'Processed {iFuture}')

    return axes_dict, thn_resos


def process_reso_sparse(iOccu, i, reso_sparse, axes, occu, axis):
    temp_reso_sparse = reso_sparse.Clone()
    
    temp_reso_sparse.GetAxis(axes['occu']).SetRange(occu[0], occu[1])
    if axis > 9:
        temp_reso_sparse.GetAxis(axes['sel1']).SetRange(1,1)
        temp_reso_sparse.GetAxis(axes['sel2']).SetRange(1,1)
        temp_reso_sparse.GetAxis(axes['sel3']).SetRange(1,1)
        temp_reso_sparse.GetAxis(axes['sel4']).SetRange(1,1)
        temp_reso_sparse.GetAxis(axes['sel5']).SetRange(1,1)
    else:
        temp_reso_sparse.GetAxis(axis).SetRange(1,1)
    
    
    hFT0cFV0a_temp = temp_reso_sparse.Projection(axes['FT0cFV0a'], axes['cent'])
    hFT0cFV0a_temp.SetName(f'hFT0cFV0a_{iOccu}_{i}')
    hFT0cFV0a_temp.SetDirectory(0)
    
    hFT0cTPCtot_temp = temp_reso_sparse.Projection(axes['FT0cTPCtot'], axes['cent'])
    hFT0cTPCtot_temp.SetName(f'hFT0cTPCtot_{iOccu}_{i}')
    hFT0cTPCtot_temp.SetDirectory(0)
    
    hFV0aTPCtot_temp = temp_reso_sparse.Projection(axes['FV0aTPCtot'], axes['cent'])
    hFV0aTPCtot_temp.SetName(f'hFV0aTPCtot_{iOccu}_{i}')
    hFV0aTPCtot_temp.SetDirectory(0)
    
    temp_reso_sparse.Delete()
    del temp_reso_sparse
    print(f'Processed {i}')
    return hFT0cFV0a_temp, hFT0cTPCtot_temp, hFV0aTPCtot_temp

def proj_reso(config_flow, axes_dict):
    
    with open(config_flow, 'r') as f:
        config = yaml.safe_load(f)
        
    reso_files = config['anresdir']
    
    for iOccu, occu in enumerate(occupancy_cut):
        if iOccu == 0:
            axes, reso_sparses = get_reso_sparses(reso_files, axes_dict['occu'], occu)

        for name, axis in axes_dict.items():
            if axis < 5:
                continue

            with ProcessPoolExecutor(24) as executor:
                futures = [
                    executor.submit(
                        process_reso_sparse,
                        iOccu,
                        i,
                        reso_sparse,
                        axes,
                        occu,
                        axis
                    )
                    for i, reso_sparse in enumerate(reso_sparses)
                ]
            results = []
            for iFuture, future in enumerate(futures):
                print(f'Processed {iFuture}')
                results.append(future.result())
            
            for i, (hFT0cFV0a_temp, hFT0cTPCtot_temp, hFV0aTPCtot_temp) in enumerate(results):
                if i == 0:
                    hFT0cFV0a = hFT0cFV0a_temp.Clone('hFT0cFV0a')
                    hFT0cFV0a.SetDirectory(0)
                    hFT0cFV0a.Reset()
                    
                    hFT0cTPCtot = hFT0cTPCtot_temp.Clone('hFT0cTPCtot')
                    hFT0cTPCtot.SetDirectory(0)
                    hFT0cTPCtot.Reset()
                    
                    hFV0aTPCtot = hFV0aTPCtot_temp.Clone('hFV0aTPCtot')
                    hFV0aTPCtot.SetDirectory(0)
                    hFV0aTPCtot.Reset()
                    
                hFT0cFV0a.Add(hFT0cFV0a_temp)
                hFT0cTPCtot.Add(hFT0cTPCtot_temp)
                hFV0aTPCtot.Add(hFV0aTPCtot_temp)

            os.makedirs(config['out_dir'], exist_ok=True)
            outfile = TFile.Open(f'{config["out_dir"]}/proj_reso_{iOccu}_{name}_{config["suffix"]}.root', 'RECREATE')
            outfile.mkdir('hf-task-flow-charm-hadrons/spReso')
            outfile.cd('hf-task-flow-charm-hadrons/spReso')
            hFT0cFV0a.Write(f'hSpResoFT0cFV0a')
            hFT0cTPCtot.Write(f'hSpResoFT0cTPCtot')
            hFV0aTPCtot.Write(f'hSpResoFV0aTPCtot')
            outfile.Close()

def process_reso(i, reso_file):
    reso = TFile.Open(reso_file, 'read')
    hFT0cFV0a_temp = reso.Get('hf-task-flow-charm-hadrons/spReso/hSpResoFT0cFV0a')
    hFT0cFV0a_temp.SetName(f'hFT0cFV0a_{i}')
    hFT0cFV0a_temp.SetDirectory(0)
    
    hFT0cTPCtot_temp = reso.Get('hf-task-flow-charm-hadrons/spReso/hSpResoFT0cTPCtot')
    hFT0cTPCtot_temp.SetName(f'hFT0cTPCtot_{i}')
    hFT0cTPCtot_temp.SetDirectory(0)
    
    hFV0aTPCtot_temp = reso.Get('hf-task-flow-charm-hadrons/spReso/hSpResoFV0aTPCtot')
    hFV0aTPCtot_temp.SetName(f'hFV0aTPCtot_{i}')
    hFV0aTPCtot_temp.SetDirectory(0)
    
    reso.Close()
    
    return hFT0cFV0a_temp, hFT0cTPCtot_temp, hFV0aTPCtot_temp

def proj_reso_tot(config_flow):
    
    with open(config_flow, 'r') as f:
        config = yaml.safe_load(f)
        
    reso_files = config['anresdir']
    
    with ProcessPoolExecutor(24) as executor:
        futures = [
            executor.submit(
                process_reso,
                i,
                reso_file,
            )
            for i, reso_file in enumerate(reso_files)
        ]
    results = []
    for iFuture, future in enumerate(futures):
        print(f'Processed {iFuture}')
        results.append(future.result())
    
    for i, (hFT0cFV0a_temp, hFT0cTPCtot_temp, hFV0aTPCtot_temp) in enumerate(results):
        if i == 0:
            hFT0cFV0a = hFT0cFV0a_temp.Clone('hFT0cFV0a')
            hFT0cFV0a.SetDirectory(0)
            hFT0cFV0a.Reset()
            
            hFT0cTPCtot = hFT0cTPCtot_temp.Clone('hFT0cTPCtot')
            hFT0cTPCtot.SetDirectory(0)
            hFT0cTPCtot.Reset()
            
            hFV0aTPCtot = hFV0aTPCtot_temp.Clone('hFV0aTPCtot')
            hFV0aTPCtot.SetDirectory(0)
            hFV0aTPCtot.Reset()
            
        hFT0cFV0a.Add(hFT0cFV0a_temp)
        hFT0cTPCtot.Add(hFT0cTPCtot_temp)
        hFV0aTPCtot.Add(hFV0aTPCtot_temp)

    os.makedirs(config['out_dir'], exist_ok=True)
    outfile = TFile.Open(f'{config["out_dir"]}/proj_reso_{config["suffix"]}.root', 'RECREATE')
    outfile.mkdir('hf-task-flow-charm-hadrons/spReso')
    outfile.cd('hf-task-flow-charm-hadrons/spReso')
    hFT0cFV0a.Write(f'hSpResoFT0cFV0a')
    hFT0cTPCtot.Write(f'hSpResoFT0cTPCtot')
    hFV0aTPCtot.Write(f'hSpResoFV0aTPCtot')
    outfile.Close()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument("config", metavar="text",
                        default="config.yaml", help="flow configuration file")
    parser.add_argument("--total", "-t", action="store_true",
                        help="use total resolution")
    
    if parser.parse_args().total:
        proj_reso_tot(
            config_flow = parser.parse_args().config
        )
    else:
        proj_reso(
            config_flow = parser.parse_args().config,
            axes_dict = axes_dict
        )
