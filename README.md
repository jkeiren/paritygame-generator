Parity game generator
=====================

This repository provides a generator for parity games that bundles different ways to generate parity games, and uses parallel processing to generate over 1000 parity games. Currently four classes of games are included: random games, synthetic games that are hard for certain algorithms, model checking problems and equivalence checking problems.

The generator also collects structural information about the parity game and stores this in the structured YAML format. For convenience some utilities are provided to check consistency of the output, and to transform the YAML data into an SQLite database. This latter database allows quick querying, and plotting of data.

The current version of the parity game generator was developed to evaluate equivalence reductions of parity games, and therefore includes the possibility to reduce games using 4 types of equivalences (see also the "thesis" tag).

Generated games
---------------
The parity games that were generated using this script, and are reported in Chapter 5 of [J.J.A. Keiren. Advanced Reduction Techniques for Model Checking. PhD thesis, Eindhoven University of Technology, 2013](http://www.jeroenkeiren.nl/wp-content/uploads/2013/10/Keiren-MSc-thesis-2009-An-experimental-study-of-algorithms-and-optimisations-for-parity-games-with-an-application-to-Boolean-Equation-Systems.pdf), can be downloaded in PGSolver format from [here](https://mega.co.nz/#F!YRxwXILY!MkV-ZEVMeVieHbgJZAf76w).

All parity games are in max parity game format, i.e. they are based on the assumption that even wins the game if the *greatest* priority that occurs infinitely often is even (opposed to min parity games in which the least priority is considered).

If you would like to add parity games to this benchmark suite, or would like to add extra statistics, feel free to contact me.

Platform requirements
---------------------
The tool is currenlty Linux-only due to the use of a platform-specific script to limit time and memory usage.

Installation
------------
Before the script can be used, all tools that are called by the tool need to be installed. We assume that the check out lives in `/path/to/paritygame-generator`. The tools can be installed by executing the following command in the root of the `paritygame-generator` directory:

    ./install_prerequisites.sh

In this case, make sure to execute the following before calling `run.py` below.

    export PATH=/path/to/paritygame-generator/tools/install/bin:$PATH
    export LD_LIBRARY_PATH=/path/to/paritygame-generator/tools/install/lib:$LD_LIBRARY_PATH

Alternatively, all tools can be installed manually; in this case you need to 
make sure that the following tools can be found in the `$PATH`.

* `gist`
* `goal`
* `lps2lts`
* `lps2pbes`
* `mcrl22lps`
* `mlsolver`
* `pbes2bes`
* `pginfo`
* `pgsolver`

Usage
-----
Experiments should be run only if the tools listed in the previous section are in the
`PATH`. Then invoke

    python run.py [-v[v[v[...]]]] [-jN] [yamlfile]
    
to run the experiments. More `v`'s means more verbose. For `N` a positive integer, `N` jobs are started if `-jN` is given. If a filename is given on the command line, results are put in that file. The file is not overwritten: if it already exists, then the experiments for which it contains results are skipped.
