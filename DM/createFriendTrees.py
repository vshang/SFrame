#! /usr/bin/env python

import os, multiprocessing, math
from array import array
from ROOT import TFile, TH1, TF1, TLorentzVector, TTree, TObject


from xsections import xsection

import optparse
usage = 'usage: %prog [options]'
parser = optparse.OptionParser(usage)
parser.add_option('-i', '--input', action='store', type='string', dest='origin', default='testout/')
parser.add_option('-t', '--treefile', action='store', type='string', dest='treefile', default='TT.root')
parser.add_option('-o', '--output', action='store', type='string', dest='target', default='testout2/')
parser.add_option('-f', '--filter', action='store', type='string', dest='filter', default='')
parser.add_option('-s', '--single', action='store_true', dest='single', default=False)
parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False)
parser.add_option('-c', '--copytree', action='store_true', dest='copytree', default=False)

(options, args) = parser.parse_args()

origin      = options.origin
target      = options.target
treefile      = options.treefile
filterset   = options.filter
singlecore  = options.single
verboseout  = options.verbose
copytree  = options.copytree

LUMI    = 35867.
ANALYSIS = "DMAnalysis"

if not os.path.exists(origin):
    print 'Origin directory', origin, 'does not exist, aborting...'
    exit()

try: os.stat(target)
except: os.mkdir(target)
try: os.stat(target+'/logs')
except: os.mkdir(target+'/logs')


##############################

def processFile(sample_name, verbose=False):
    sample = sample_name.replace(ANALYSIS+".", "").replace(".root", "")
    isMC = not '2016' in sample
    
    # Unweighted input
    ref_file_name = origin + '/' + sample_name
    if not os.path.exists(ref_file_name): 
        print '  WARNING: file', ref_file_name, 'does not exist, continuing'
        return True
    
    # Weighted output
    new_file_name = target + '/' + sample + '.root'
    #if os.path.exists(new_file_name):
    #    print '  WARNING: weighted file exists, overwriting'
        #return True
    
    new_file = TFile(new_file_name, 'RECREATE')
    new_file.cd()
    
    # Open old file
    ref_file = TFile(ref_file_name, 'READ')
    ref_hist = ref_file.Get('Events')
    try:
        totalEntries = ref_hist.GetBinContent(1)
    except:
        print '  ERROR: nEvents not found in file', sample
        exit(1)

    old_tree = ref_file.Get("tree")
    #check if the tree already has the lumi weights    
    hasLumiWeights = any(True for x in old_tree.GetListOfBranches() if "eventWeightLumi" in x.GetName())

    # Cross section
    
    XS = xsection[sample]['xsec']*xsection[sample]['kfactor']*xsection[sample]['br']
    Leq = LUMI*XS/totalEntries if totalEntries > 0 else 0.
    
    print sample, ": Leq =", (Leq if isMC else "Data")
    
    for key in ref_file.GetListOfKeys():
        obj = key.ReadObj()
        # Histograms
        if obj.IsA().InheritsFrom('TH1'):
            if verbose: print ' + TH1:', obj.GetName()
            new_file.cd()
            if isMC and not hasLumiWeights: obj.Scale(LUMI*XS/totalEntries)
            obj.Write()
        # Tree
        elif obj.IsA().InheritsFrom('TTree'):
            continue
        # Directories
        elif obj.IsFolder():
            subdir = obj.GetName()
            if verbose: print ' \ Directory', subdir, ':'
            new_file.mkdir(subdir)
            new_file.cd(subdir)
            for subkey in ref_file.GetDirectory(subdir).GetListOfKeys():
                subobj = subkey.ReadObj()
                if subobj.IsA().InheritsFrom('TH1'):
                    if verbose: print '   + TH1:', subobj.GetName()
                    new_file.cd(subdir)
                    if isMC and not hasLumiWeights: subobj.Scale(LUMI*XS/totalEntries)
                    subobj.Write()
            new_file.cd('..')
        

    # Variables declaration
    dummy = array('f', [1.0]) #example variable
    stitchWeight = array('f', [1.0])
    eventWeightLumi = array('f', [1.0])  # global event weight with lumi


    nev = old_tree.GetEntriesFast()
    new_file.cd()
    
    #we are not going to copy the entire old tree
    tname = "Ftree"
    new_tree = TTree(tname,tname)
    if copytree:
        tname = "tree"
        new_tree = old_tree.CopyTree("")

    #define new branches you want to add here
    #!!!Attention: if run twice, this will create a new branch with the same name as the old one
    dummyBranch = new_tree.Branch('dummy', dummy, 'dummy/F')
    if not (hasLumiWeights): #only do lumi branches if they don't exist already
        stitchWeightBranch = new_tree.Branch('stitchWeight', stitchWeight, 'stitchWeight/F')
        eventWeightLumiBranch = new_tree.Branch('eventWeightLumi', eventWeightLumi, 'eventWeightLumi/F')

    
    
    # looping over events
    for event in range(0, old_tree.GetEntries()):
        if verbose and (event%10000==0 or event==nev-1): print ' = TTree:', old_tree.GetName(), 'events:', nev, '\t', int(100*float(event+1)/float(nev)), '%\r',
        old_tree.GetEntry(event)

        #calculate new variable and fill
        dummy[0] = 1


        if not (hasLumiWeights):
            eventWeightLumi[0] = stitchWeight[0] = 1
        if isMC:
            # MC stitching
            if sample=='DYJetsToLL' or sample=='WJetsToLNu' or sample=='W1JetsToLNu' or sample=='W2JetsToLNu' or sample=='W3JetsToLNu' or sample=='W4JetsToLNu':
                if old_tree.LheHT > 70.: stitchWeight[0] = 0.
            if not (hasLumiWeights):
                eventWeightLumi[0] = old_tree.eventWeight * old_tree.bTagWeight * old_tree.TopWeight
                eventWeightLumi[0] *= LUMI*XS/totalEntries

            #fill the new branches of the tree
            if not (hasLumiWeights):
                if copytree:
                    stitchWeightBranch.Fill()
                    eventWeightLumiBranch.Fill()

        if copytree:
            dummyBranch.Fill()
        else:
            new_tree.Fill()

    new_file.cd()
    new_tree.Write(tname,TObject.kOverwrite)
    if verbose: print ' '
    new_file.Close() 


if __name__ == "__main__":
    
    if not treefile.replace(ANALYSIS+".", "").replace(".root", "") in xsection.keys(): exit
    processFile(treefile, verboseout)
    
