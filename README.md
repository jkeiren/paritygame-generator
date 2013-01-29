Parity game generator
=====================

Generator for parity games using various generation techniques to obtain a broad range of games.

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
Experiments should run iff the tools listed in the previous section are in the
`PATH`. Then invoke

    python run.py [-v[v[v[...]]]] [-jN] [yamlfile]
    
to run the experiments. More `v`'s means more verbose. For `N` a positive integer, `N` jobs are started if `-jN` is given. If a filename is given on the command line, results are put in that file. The file is not overwritten: if it already exists, then the experiments for which it contains results are skipped.
