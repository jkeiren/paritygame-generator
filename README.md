Parity game generator
=====================

Generator for parity games using various generation techniques to obtain a broad class of games

Usage
=====
Experiments should run iff the pgsolver, mcrl2 and pgconvert binaries
are in the PATH. Then invoke
> python run.py [-v[v[v[...]]]] [-jN] [yamlfile]
to run the experiments. More v's means more verbose. For N a positive
integer, N jobs are started if -jN is given. If a filename is given on
the command line, results are put in that file. The file is not 
overwritten: if it already exists, then the experiments for which it
contains results are skipped.
