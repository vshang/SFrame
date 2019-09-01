# SFrame Repository (Victor's copy)

## Step-by-step guide to installation

### Step 0: ROOT and CMSSW enviroments

Set up the ROOT environment at PSI. The easiest way to do that is to run the `cmsenv` commend in a previously installed CMSSW release (now using CMSSW_8_0_26_patch1).

```
source /swshare/psit3/etc/profile.d/cms_ui_env.sh
source $VO_CMS_SW_DIR/cmsset_default.sh
CMSSW_8_0_26_patch1
cd CMSSW_8_0_26_patch1/src
cmsenv
```

### Step 1: Download and setup SFrame

Clone the git repository. Navigate to your work directory, preferably not in a CMSSW release, and run
```bash
git clone https://github.com/zucchett/SFrame.git
cd SFrame
git remote add mysframe https://github.com/YOUR-USERNAME/SFrame.git

```
and enter the `SFrame` directory.
Then, setup the SFrame environment. In the `SFrame` directory, run the `setup.sh` script:
```bash
cd SFrame/
source setup.sh
cd ..
```

### Step 2: Compile packages

Before running the code, it is necessary to compile all packages. For this run:
```bash
./makeAll.sh
```
you can also go into each directory starting with `SFrame` and type `make`
Remember that, in case you perform significant modifications to SFrame like adding new variables, adding new methods to classes, adding new packages, it's often useful to clear compiled objects with the `make distclean` command, and then recompile with `make`. If you want to clean everything use `./makecleanAll.sh`



## How to run the code

There are two running modes, locally or with the batch system. The former is used for debugging, checking the output before moving to mass production, and running on small files. The batch mode is used to run on large amount of files such as data and backgrounds. This mode curretly works only on the UZH cluster.

### Local mode

Enter your package, and compile it with the `make` command.
Then, set up your configuration xml file. The configuration files are located in the `config` directory, and include the list of packages to be loaded by SFrame, the package parameters, the verbosity level, and the ntuple file to be read.
Once the configuration file is set, and points to a readable rootfile, the code can be run with the command:
```bash
cd DM
make
sframe_main config/Configfile.xml
```
where `Configfile.xml` is the name of the desired configuration file.


### Batch mode

Before running the batch mode, please make sure that the code runs and produce meaningful results. Do not run in batch mode for testing, as it will create a lot of processes.
In order to acces files not stored on the tier3, make sure to create a valid grid proxy with the command:
```bash
voms-proxy-init --voms cms
```

The batch jobs are divided in several blocks, to allow some flexibility and run on a subset of the samples (for instance, you may want to run on data alone without processing MC). Each block has a `submitBlock.py` file, which constains approximately the same information provided by the `.xml` configuration files.
Submit the desired block with the command:
```bash
python -u submitSFrame.py -j submitBlock.py --nosandbox --useEnvironment --keepTemp &> logBlock.txt &
```
where `Block` replaces the block name. The commands to run all blocks in once is in the `submitAll.sh` file. Handle with care!

You can check the status of each block with the `tail -f logBlock.txt` command.

Once the logfiles end with `Tschoe!` line, the jobs have finished. The temporary outputs can be found in the `AnalysisTemp` directory, and the merged outputs in the `AnalysisOutput` directory. If the latter is empty, and the jobs have finished, checking the temporary files and logs is a good strating point to understand what has gone wrong.



### Post-processing (old option)

The post-processing script `addWeight.py` is also included. The simplest post-processing step consists in adding a new variable to the tree containing the weight relatove to each single event, by accounting for the equivalent luminosity and the cross section of the sample.
The cross sections are taken from the `xsection.py` file, which is included by `addWeight.py`. Control histograms are rescaled as well. If needed, the post-processing step may be extended to perform more complicate operations, such as calculating multivariate discriminants.
The script accepts as argument a filter list with the `-f filterlist` where a string to filter input files may be also provided. The output directory should be also specified with the `-o` parameter, or the default direcotry should already exist.
By default, the post-processing is performed in parallel between different samples, to expolit multi-core machines. The post-processing can be lauched with the command:
```bash
python addWeight.py
```

### Post-processing (newer option)
We have added a script (very similar to addWeights.py) that can be run instead and all jobs can be submitted to the batch system.
```bash
python submitFriendTrees.py -i INPUT_SFRAME_NTUPLES/ -o testout (-c True)
```
This code does the same as addWeights, but the default is to just create a friendtree that can be used in addition to the usual tree.
If the option `-c True` is used the the input tree is copied. Running the code over already weighted files will not weight them again, there
is a protection against that, however avoid it since it can causer other problems. 
Working with Friendtrees:
```bash
root -l OldTreeFile.root
TTree *T  = (TTree*)_file0->Get("tree")
TFile *_FriendTree = TFile::Open("FriendTreeFile.root")
TTree *FT  = (TTree*)_FriendTree->Get("Ftree")
T->AddFriend(FT)
T->Draw("bla","bli","blub")
```

### Plotting
Once all ntuples are processed, you can plot variables. The tools for this are located in the `Plotting` directory.
```
cd Plotting
mkdir plot
python plot.py -v "variable_name as in variables.py" -c "cut name as in selections.py"
```