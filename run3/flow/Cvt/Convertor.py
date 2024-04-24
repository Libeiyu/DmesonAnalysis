import argparse
import ROOT
import array
import os

# Check if the file exists
if os.path.exists("ConvertorResult.root"):
    # If the file exists, remove it
    os.remove("ConvertorResult.root")
    print("File ConvertorResult.root was removed successfully.")
else:
    # If the file does not exist, print a message
    print("File ConvertorResult.root does not exist.")

def convertor(output_run2):

    path_run2 = 'PWGHF_D2H_HFvn_Dzero_v2_3050_MLappVZEROC_EvShapeSP/coutputvnDzero_v2_3050_MLappVZEROC_EvShapeSP'
    #list_run2= 'coutputvnDzero_v2_3050_MLappVZEROC_EvShapeSP'
    path = 'hf-task-flow-charm-hadrons/'
    sub_path = 'spReso/' 
    prefix = 'SpReso'

    infile = ROOT.TFile(output_run2, 'READ')

    keys = infile.GetListOfKeys()
    for key in keys:
        if key.GetClassName() == 'TDirectoryFile':
            print(key.GetName())
            directory = key.ReadObj()
            subkeys = directory.GetListOfKeys()
            for subkey in subkeys:
                if subkey.GetClassName() == 'TList':
                    print(subkey.GetName())

    hist_SPvsQnvsCent, hist_SP_proj_cent, thn_run2 = [], [], []
    dets = ['FT0cFT0a', 'FT0cTPCpos', 'FT0aTPCpos']
    emptydets = ['hSpResoFT0cFV0a', 'hSpResoFT0cTPCneg', 'hSpResoFT0aFV0a', 'hSpResoFT0aTPCneg', 'hSpResoFT0mFV0a', 'hSpResoFT0mTPCpos', 'hSpResoFT0mTPCneg', 'hSpResoFV0aTPCpos', 'hSpResoFV0aTPCneg', 'hSpResoTPCposTPCneg']

    #nbins = array.array('i', [100, 10, 10000, 100, 100, 100, 1000, 1000, 1000])
    #xmin = array.array('d', [1.78, 0., 0., -1., -1., 0., 0., 0., 0.])
    #xmax = array.array('d', [2.05, 10., 100., 1., 1., 1., 1., 1., 1.])
    #thn_run3 = ROOT.THnSparseT(ROOT.TArrayF)("hSparseFlowCharm", "THn for SP", len(nbins), nbins, xmin, xmax)

    #thn_run3.GetAxis(0).SetName("Inv. mass (GeV/#it{c}^{2})")
    #thn_run3.GetAxis(1).SetName("#it{p}_{T} (GeV/#it{c})")
    #thn_run3.GetAxis(2).SetName("Centrality")
    #thn_run3.GetAxis(3).SetName("cos(%d#varphi)" % 2)  #
    #thn_run3.GetAxis(4).SetName("cos(%d(#varphi - #Psi_{sub}))" % 2)
    #thn_run3.GetAxis(5).SetName("SP")
    #thn_run3.GetAxis(6).SetName("1 score")
    #thn_run3.GetAxis(7).SetName("2 score")
    #thn_run3.GetAxis(8).SetName("3 score")
    #thn_run2_order = [0, 1, 6, 3, 4, 2, 9, 10, 11]

    outfile = ROOT.TFile("ConvertorResult.root", 'RECREATE')
    outfile.cd()
    outfile.mkdir("run2")
    outfile.mkdir(f'{path}{sub_path}')
    #Resolution
    for iResHist in range(1, 4):
        outfile.cd("run2")
        hist_SPvsQnvsCent.append(infile.Get(f'{path_run2}').FindObject(f'hScalProdQnVectors{iResHist}'))
        hist_SPvsQnvsCent[-1].SetDirectory(outfile)
        hist_SPvsQnvsCent[-1].Write()

        outfile.cd(f'{path}{sub_path}')
        hist_SP_proj_cent.append(hist_SPvsQnvsCent[-1].Project3D("zx"))
        # 获取旧直方图的内容和误差
        old_hist = hist_SP_proj_cent[-1]
        nbinsX = old_hist.GetNbinsX()
        nbinsY = old_hist.GetNbinsY()

        # 创建一个新的二维直方图，X轴范围从0到100，Y轴保持不变
        new_hist = ROOT.TH2F("new_hist", "new_hist", 100, 0, 100, nbinsY, old_hist.GetYaxis().GetXmin(), old_hist.GetYaxis().GetXmax())

        # 将旧直方图的内容复制到新的直方图中
        for i in range(1, nbinsX+1):
            for j in range(1, nbinsY+1):
                bin_content = old_hist.GetBinContent(i, j)
                bin_error = old_hist.GetBinError(i, j)
                new_binX = new_hist.GetXaxis().FindBin(old_hist.GetXaxis().GetBinCenter(i))
                new_binY = new_hist.GetYaxis().FindBin(old_hist.GetYaxis().GetBinCenter(j))
                new_hist.SetBinContent(new_binX, new_binY, bin_content)
                new_hist.SetBinError(new_binX, new_binY, bin_error)

        # 将新的直方图写入到文件中
        new_hist.SetName(f'h{prefix}{dets[iResHist-1]}')
        new_hist.Write()
        #new_hist.SetDirectory(outfile)

    for name in emptydets:
        outfile.cd(f'{path}{sub_path}')
        hist = ROOT.TH2F(name, name, 100, 0, 100, 100, 0, 1)
        hist.Write()
    # THnSparse
    outfile.cd("run2")
    thn_run2 = infile.Get(f'{path_run2}').FindObject('fHistMassPtPhiqnCentr')
    #thn_run2[-1].SetDirectory(outfile)
    thn_run2.Write()
    outfile.cd(f'{path}')
    #for i in thn_run2_order:
    #    bin_content = thn_run2.GetBinContent(i)
    #    coords = array.array('d', [thn_run2.GetAxis(i).GetBinCenter(i)])
    #    thn_run3.Fill(coords, bin_content)
    thn_run2.SetName('hSparseFlowCharm')
    #thn_run2[-1].SetDirectory(outfile)
    thn_run2.Write()

    infile.Close()
    outfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument("output_run2", metavar="text",
                        default="AnalysisResults.root", help="input ROOT file from run2")
    args = parser.parse_args()

    convertor(
        output_run2=args.output_run2,
    )