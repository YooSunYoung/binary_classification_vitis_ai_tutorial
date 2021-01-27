# Vitis-AI Tutorial for Binary Classification with Tensorflow

### 1. Prepare for the data to use
   
In this tutorial, I will use MRL eyes images.
data can be found at [https://mrl.cs.vsb.cz](https://mrl.cs.vsb.cz).
<br>
Explanation of the data is also in the zip file.
I will assume you extract the zip file in the directory  `./data/`
   
### 2. AI Model Training and Freeze Model
    
`simple_net.py` can be divided into 5 sections.
1. Data preprocess
2. Neural network design
3. Model train
4. Model test
5. Freeze model

As a result, you should have `model.pb` file which is frozen weight including
 the information of the graph of the model.
I used tensorflow version 1.5 since some Models for tensorflow version 2 are not supported by vitis-ai.

### 3. Docker Environment for Vitis-AI

You need to install docker to use vitis-ai since we are going to use vitis-ai on docker environment.
The image can be pulled from [https://hub.docker.com/r/xilinx/vitis-ai](https://hub.docker.com/r/xilinx/vitis-ai).

Docker run script can be found [https://github.com/Xilinx/Vitis-AI](https://github.com/Xilinx/Vitis-AI).
This script mount the current directory as `/workspace/` in the container.
In the docker environment, you should have `object_detection` directory of this project in your workspace.

This virtual environment has virtual environments in it. You have to activate conda environment for tensorflow.

```
conda activate vitis-ai-tensorflow
```

Then you should move some images and make directories.
Directories can be made by `object_detection/setenv.sh`.
Images of the eyes should be copied into `object_detection/img/` directory.
I couldn't be bothered to make script for this, sorry.
Once you finished moving images you want to use for calibration, you can run 
```
ls img/ > calib_list.txt
```
to have the list of images for calibration.

Also, you should have your `model.pb` in the `object_detection/` directory.
Now you are ready to move on.

## 4. Model Quantization

`object_detection/quantize_recipe.sh` has the command recipe for `vai-q-tensorflow quantize` command. 
You can find the name of the input/output layer in `simple_net.py`.

You will have quantized frozen model in `quantize_results/`

## 5. Compile DPU Executable

`compile.sh` compiles the frozen, quantized model into DPU executable files.

You will have results in `output/`

You need to copy the output files into `target/` directory.

```
cp output/* target/
```

## 6. FPGA

Now you should move the `object_detection/target` directory into the ZYNQ board.
I used `ZCU-102` board.

On FPGA, you should compile again, with `target/compile.sh`.

Then you can run `app.py` with command
```
python3 app.py -j /home/root/target/dpuv2_rundir/ -i images/
```
Don't forget to use `python3`.