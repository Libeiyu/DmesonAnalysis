#Parameters
#----------

#- config (str): path of directory with config files
#- an_res_file (str): path of directory with analysis results
#- centrality (str): centrality class
#- resolution (str/int): resolution file or resolution value
#- outputdir (str): output directory
#- suffix (str): suffix for output files
#- vn_method (str): vn technique (sp, ep, deltaphi)
#- wagon_id (str): wagon ID
#- skip_resolution (bool): skip resolution extraction
#- skip_projection (bool): skip projection extraction
#- skip_vn (bool): skip raw yield extraction
#----------

# resutls will be saved in ${workdir}/Results/${dataCent}/${centrality}/${size}/
scriptdir=$(dirname $0)
workdir=/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/reso
config=/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/config/config_flow_RESO.yml

centrality=k6080 # k020 k3050 k6080  <-----------------------------------------------------------------------------------------------
dataCent=0100 # 020 2050 50100   <---------------------------------------------------------------------------------------------------
size=large # small medium large <-------------------------------------------------------------------------------------------------------
vn_method=sp # sp ep deltaphi   <---------------------------------------------------------------------------------------------------
qvec= # full recenter   <-------------------------------------------------------------------------------------------------------
debug=ini_occu #_old #_new #_tot

wagon_id= # 13649 14351 13650 14352    <---------------------------------------------------------------------------------------
doReso=true # false true    <-------------------------------------------------------------------------------------------------------
doProj=false # false true

an_res_file="/home/wuct/ALICE/local/reso/DmesonAnalysis/run3/flow/reso/k3050/third/proj_reso_3_occupancy.root
"

resolution=path/to/resolution.root

if [ ! -z "$wagon_id" ]; then wagon="-w ${wagon_id}" ; else wagon="" ; fi

# suffix
cent="${centrality:1}"
siz="${size:0:1}"
qve="${qvec:0:2}"
suffix=${cent}${siz}_${qve}${debug}

if $doReso; then
    reso="--skip_projection --skip_vn"
    suffix=${suffix}_Reso
else 
    reso="-r ${resolution} --skip_resolution" 
fi

if $doProj; then
    proj="--skip_resolution --skip_vn"
    suffix=${suffix}_Proj
else
    proj=""
fi

# output dir.
outputdir=${workdir}/Results/${dataCent}/${centrality}/${size}/
echo "Output directory: ${outputdir}"
if [ ! -d "${outputdir}" ]; then mkdir -p ${outputdir}; fi

    python3 ${scriptdir}/run_full_flow_analysis.py \
    ${config} \
    ${an_res_file} \
    -c ${centrality} \
    -o ${outputdir} \
    -s ${suffix} \
    -v ${vn_method} \
    ${reso} \
    ${wagon} \
    $proj \
    --skip_efficiency \
    #--skip_projection

if [ ! -z "$wagon_id" ]; then
    cp -rf ${outputdir}/${wagon_id}/*  ${outputdir}
    rm -rf ${outputdir}/${wagon_id}
fi

