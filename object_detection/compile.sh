compile() {
    vai_c_tensorflow \
	--frozen_pb ./quantize_results/deploy_model.pb \
	--arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \
	--output_dir ./output/ \
	--net_name simple_net \
	--options "{'mode':'normal'}" 
#	--frozen_pb ./model.pb 
}

compile | tee ./log/compile_log_zcu102
#--arch /opt/vitis_ai/compiler/arch/dpuv2/ZCU102/ZCU102.json \
