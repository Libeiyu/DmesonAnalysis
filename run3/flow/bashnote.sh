#!  /bin/sh

workdir="/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow"

echo "Please enter a number:"
read number

case $number in
1)
    # resolution with different event selections and occupancy intervals
    cd $workdir
    python3 compute_reso_thn.py /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/config/config_flow_RESO.yml
;;
2)
    # estiamte the resolution with projections
    cd $workdir
    outputdir="/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/reso/Results"

    projs_qvec=($(find "/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/reso/k3050/third" -type f))
    for proj_qvec in ${projs_qvec[@]}; do
        echo "Processing $proj_qvec"
        suffix=$(basename $proj_qvec)
        python3 compute_reso.py "$proj_qvec" -c "k3050" -o "$outputdir" -s "$suffix"
    done
;;


3)
    # compare the resolutions
    cd "/home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons"
    python3 /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/CompareGraphs.py /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/config_comparison_occu_evt_reso.yml

;;
4)
    # compute the resolution with different event selections and occupancy intervals
    cd /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT
    bash /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT/run_cutvar.sh
;;
5)
    # run the full flow analysis
    cd /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT
    configs=($(find "/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/config" -type f -name "*_sel*.yml"))
    for config in ${configs[@]}; do
        echo "Processing $config"
        bash /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT/run_cutvar.sh $config
    done
;;
6)
    # run the full flow analysis
    cd "/home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons"
    python3 /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/CompareGraphs.py /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/config_comparison_evtsel_v2.yml
;;
7)
    # run the full flow analysis
    cd /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT
    configs=($(find "/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/config" -type f -name "*_eff*.yml"))
    for config in ${configs[@]}; do
        echo "Processing $config"
        bash /home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/BDT/run_cutvar_eff.sh $config
    done
;;
8)
    # run the full flow analysis
    cd "/home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons"
    python3 /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/CompareGraphs.py /home/wuct/ALICE/local/reso/DmesonAnalysis/comparisons/config_comparison_eff.yml
;;
*)
    echo "Invalid option"
    exit 1
;;
esac






