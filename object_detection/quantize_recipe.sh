vai_q_tensorflow quantize \
	--input_frozen_graph model.pb \
	--input_nodes normalized_gray_image \
	--input_shapes ?,50,50,1 \
	--output_nodes  final_output \
	--input_fn input_fn.calib_input \
	--method 0 \
	--gpu 0 \
	--calib_iter 30 \
	--output_dir ./quantize_results \
	--weight_bit 8 \
	--activation_bit 8 \


