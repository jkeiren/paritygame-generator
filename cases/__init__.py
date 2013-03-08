import multiprocessing
import logging
import traceback
import tempfile
import os
import re
import tools
import pool
import sys
import yaml
from tools import OutOfMemory, Timeout

LARGE_GRAPH=100000

TIMEOUT = 12*60*60 # 12 hours for getting info
LPSTOOLS_TIMEOUT = TIMEOUT
MLSOLVER_TIMEOUT= 60*60
PBES2BES_TIMEOUT = TIMEOUT
PGINFO_TIMEOUT = 120*60
PGSOLVER_TIMEOUT= TIMEOUT
SOLVE_TIMEOUT = 60*60 # 1 hour for solving

MEMLIMIT = 128*1024*1024 # memory limit in kbytes
LPSTOOLS_MEMLIMIT = 8*1024*1024
MLSOLVER_MEMLIMIT = MEMLIMIT
PBES2BES_MEMLIMIT = MEMLIMIT
PGINFO_MEMLIMIT = MEMLIMIT
PGSOLVER_MEMLIMIT = MEMLIMIT
SOLVE_MEMLIMIT = MEMLIMIT

RETURN_EXISTING = True

def cleanResult(result):
  '''Clean result for saving the output, i.e. remove stdout and stderr output
     from the dictionary if desired'''
  del result['out']
  del result['err']
  return result

class TempObj(pool.Task):
  def __init__(self):
    super(TempObj, self).__init__()
    self._temppath = '.'
    self._prefix = ""

  def __escape(self, s):
    return s.replace('/', '_').replace(' ', '_')
  
  def _name(self, ext, extraprefix=""):
    return self._temppath + '/' + self.__escape(self._prefix) + extraprefix + '.' + ext
  
  def _existingTempFile(self, ext, extraprefix=""):
    if os.path.exists(self._name(ext, extraprefix)) and os.path.getsize(self._name(ext, extraprefix)) > 0:
      return self._name(ext, extraprefix)
    else:
      return None
    
  def _newTempFileDir(self, temppath, ext, extraprefix=""):
    if not os.path.exists(temppath):
      os.makedirs(temppath)
    name = self._name(ext, extraprefix)
    if self._prefix <> "" and not os.path.exists(name):
      fn = open(name, 'w+b')
      return fn
    else:
      return tempfile.NamedTemporaryFile(dir=temppath, prefix=self.__escape(self._prefix)+extraprefix, suffix='.'+ext, delete=False)
  
  def _newTempFile(self, ext, extraprefix=""):
    return self._newTempFileDir(self._temppath, ext, extraprefix)
    
  def _newTempFilenameDir(self, temppath, ext, extraprefix=""):
    fn = self._newTempFileDir(temppath, ext, extraprefix)
    fn.close()
    return fn.name
  
  def _newTempFilename(self, ext, extraprefix=""):
    return self._newTempFilenameDir(self._temppath, ext, extraprefix)

class PGInfoTask(TempObj):
  def __init__(self, pgfile, option, prefix, temppath, outdir):
    super(PGInfoTask, self).__init__()
    self.__pgfile = pgfile
    self.__option = option
    self._prefix = prefix
    self._temppath = temppath
    self._outdir = outdir
    self.result = {}
    self.result['pginfo'] = None
    self.result['yamlfile'] = None
    self.result['option'] = self.__option
    
  def phase0(self, log):
    yamlfile = self._newTempFilename("yaml")
    try:
      if self.__option in ['bfs', 'dfs']:
        log.warning("Not recording Queue/Stack sizes if number of vertices exceeds {0}".format(LARGE_GRAPH))
      result = tools.pginfo('-v', self.__pgfile, yamlfile, '--{0}'.format(self.__option), '--max-for-expensive={0}'.format(LARGE_GRAPH), memlimit=PGINFO_MEMLIMIT, timeout=PGINFO_TIMEOUT, timed=True)

    except (Timeout, OutOfMemory) as e:
      # Handle gracefully, recording the output using the normal ways
      result = e.result
      
    self.result['pginfo'] = cleanResult(result)
    self.result['output'] = yaml.load(open(yamlfile).read())
    os.unlink(yamlfile)


class PGInfoTaskGroup(TempObj):
  def __init__(self, pgfile, prefix, temppath, outdir):
    super(PGInfoTaskGroup, self).__init__()
    self._prefix = prefix
    self._temppath = temppath
    self._outdir = outdir
    
    self.__pgfile = pgfile
    
    self.result = {}
    # Map all options to the string with which they are indexed in the
    # resulting YAML output of pginfo.
    self.__optmap = {}
    self.__optmap["graph"] = "Graph"
    self.__optmap["bfs"] = "BFS"
    self.__optmap["dfs"] = "DFS"
    self.__optmap["diameter"] = "Diameter"
    self.__optmap["girth"] = "Girth"
    self.__optmap["diamonds"] = "Diamonds"
    self.__optmap["treewidth-lb"] = "Treewidth (Lower bound)"
    self.__optmap["treewidth-ub"] = "Treewidth (Upper bound)"
    self.__optmap["kellywidth-ub"] = "Kelly-width (Upper bound)"
    self.__optmap["sccs"] = "SCC"
    self.__optmap["ad-cks"] = "Alternation depth [CKS93]"
    self.__optmap["ad"] = "Alternation depth (priority ordering)"
    self.__optmap["neighbourhoods=3"] = "Neighbourhood"

  def phase0(self, log):
    log.debug('Collecting information from {0}'.format(self))
    for opt in self.__optmap:
      self.subtasks.append(PGInfoTask(self.__pgfile, opt, self._prefix, self._temppath, self._outdir))
    
  def phase1(self, log):
    log.debug('Collecting results from {0}'.format(self))
    data = {}
    for r in self.results:
      if 'output' in r.result.keys() and r.result['output']:
        assert(len(r.result['output']) == 1)
        assert(r.result['output'].keys()[0] == self.__optmap[r.result['option']])
        (k,v) = r.result['output'].items()[0]
        
        if isinstance(v, dict):
          data[k] = v
        else:
          data[k] = {}
          data[k]['value'] = v
      
          
        data[k]['times'] = r.result['pginfo']['times']
        data[k]['memory'] = r.result['pginfo']['memory']
      else: # No output recorded
        k = self.__optmap[r.result['option']]
        data[k] = {}
        data[k]['times'] = r.result['pginfo']['times']
        data[k]['memory'] = r.result['pginfo']['memory']
    
    name = self._newTempFilenameDir(self._outdir, 'yaml')
    yamlfile = open(name, 'w')
    yamlfile.write(yaml.dump(data, default_flow_style = False))
    yamlfile.close()
    self.result['pginfo']['datafile'] = name

class SolveTask(pool.Task):
  def __init__(self, name, filename, *args):
    super(SolveTask, self).__init__()
    self.__pgfile = filename
    self.__opts = list(args)
    self.result = {}
    self.result['times'] = 'unknown'
    self.result['sizes'] = 'unknown'
    self.result['solution'] = 'unknown'
    self.name = name
  
  def run(self, log):
    if self.name.startswith('pbespgsolve'):
      self.run_pbespgsolve(log)
    else:
      self.run_pgsolver(log)
  
  def run_pbespgsolve(self, log):
    try:      
      result = tools.pbespgsolve(self.__pgfile, *self.__opts, timed=True, timeout=SOLVE_TIMEOUT)
      self.result['times'] = result['times']
      self.result['solution'] = result['out'].strip()
    except tools.Timeout:
      log.info('Timeout')
      self.result['times'] = 'timeout'
  
  def run_pgsolver(self, log):
    try:
      opts = self.__opts + ['-v', '2', self.__pgfile]
      result = tools.pgsolver(*opts, timeout=SOLVE_TIMEOUT)
      self.result['times'] = re.search('Overall\s*\|.*?\s+([0-9.]+) sec', result['out'], re.DOTALL).group(1)
      self.result['solution'] = re.search('Player (0|1) wins from nodes:[^}]*?[{,]0[,}]', result['out'], re.DOTALL).group(1)
      self.result['solution'] = 'true' if self.result['solution'] == '0' else 'false'
    except tools.Timeout:
      log.info('Timeout')
      self.result['times'] = 'timeout'  

class PGCase(TempObj):
  def __init__(self):
    super(PGCase, self).__init__()
    self.result = {}
    self.result['statistics'] = {}
    self.result['solutions'] = {}
    self.result['sizes'] = {}
    self.result['times'] = {}
    self._outdir = os.path.join(os.path.split(__file__)[0], 'data')
    self.__solvepg = None
    self.__solvebes = None
    self.__error = False

  def _makePGfile(self, log, overwriteExisting):
    raise NotImplementedError()
  
  def __collectResults(self, name):
    for task in self.results:
      if task.result.has_key('solution'):
        self.result['times'].setdefault(name, {})[task.name] = task.result['times']
        self.result['solutions'].setdefault(name, {})[task.name] = task.result['solution']
      else:
        self.result['files'].setdefault(name, {})[task.name] = task.result['file']
  
  def __info(self, pgfile):
    self.subtasks.append(PGInfoTaskGroup(pgfile, self._prefix, self._temppath, self._outdir))

  def __reduce(self, pgfile, equiv):
    '''Reduce the PG modulo equiv using pgconvert.'''
    reduced = self._newTempFilename('gm')
    result = tools.pgconvert('-ve{0}'.format(equiv), pgfile, reduced, timed=True)
    self.result['sizes']['orig'] = {'vertices': result['filter']['vorig'], 'edges': result['filter']['eorig']}
    self.result['sizes'][equiv] = {'vertices': result['filter']['vred'], 'edges': result['filter']['ered']}
    self.result['times'].setdefault(equiv, {})['reduction'] = result['times']#['reduction']
    return reduced

  def __solve(self, pgfile):
    '''Solve besfile using pbsespgsolve and pgsolver.'''
    self.subtasks = [
      SolveTask('pbespgsolve', pgfile, '-srecursive')
#      SolveTask('pbespgsolve (spm)', pgfile),
#      SolveTask('pbespgsolve (recursive)', pgfile, '-srecursive'),
#      SolveTask('pgsolver (optimized spm)', pgfile, '-sp'),
#      SolveTask('pgsolver (optimized recursive)', pgfile, '-re'),
#      SolveTask('pgsolver (optimized bigstep)', pgfile, '-bs'),
#      SolveTask('pgsolver (optimized strategy improvement)', pgfile, '-si'),
#      SolveTask('pgsolver (unoptimized spm)', pgfile, '-sp', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized recursive)', pgfile, '-re', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized bigstep)', pgfile, '-bs', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized strategy improvement)', pgfile, '-si', '-dgo', '-dsg', '-dlo')
    ]

  def phase0(self, log):
    try:
      self.__pgfile = self._makePGfile(log, RETURN_EXISTING)
    except (Timeout, OutOfMemory):
      # If parity game generation fails due to timeout or out of memory,
      # we still record it in the output.
      # Therefore we need to make sure that the exception does not get through
      # to the calling layers.
      self.__error = True
      pass
    
    log.debug('Collecting information from original {0}'.format(self))
    self.__info(self.__pgfile)
    log.debug('Solving original {0}'.format(self))
    self.__solve(self.__pgfile)
  
  def phase1(self, log):
    self.__collectResults('original')
    log.debug('Reducing original modulo bisim ({0})'.format(self))
    self._prefix = self._prefix + '_bisim'
    bisimpg = self.__reduce(self.__pgfile, 'bisim')
    log.debug('Collecting information from bisim {0}'.format(self))
    self.__info(bisimpg)
    log.debug('Solving stut {0}'.format(self))
    self.__solve(bisimpg)
  
  def phase2(self, log):
    self.__collectResults('bisim')
    log.debug('Reducing original modulo  ({0})'.format(self))
    self._prefix = self._prefix.replace('_bisim', '_fmib')
    fmibpg = self.__reduce(self.__pgfile, 'fmib')
    log.debug('Collecting information from fmib {0}'.format(self))
    self.__info(fmibpg)
    log.debug('Solving fmib {0}'.format(self))
    self.__solve(fmibpg)
      
  def phase3(self, log):
    self.__collectResults('fmib')
    log.debug('Reducing original modulo  ({0})'.format(self))
    self._prefix = self._prefix.replace('_fmib', '_stut')
    stutpg = self.__reduce(self.__pgfile, 'stut')
    log.debug('Collecting information from stut {0}'.format(self))
    self.__info(stutpg)
    log.debug('Solving stut {0}'.format(self))
    self.__solve(stutpg)
      
  def phase4(self, log):
    self.__collectResults('stut')
    log.debug('Reducing original modulo  ({0})'.format(self))
    self._prefix = self._prefix.replace('_stut', '_gstut')
    gstutpg = self.__reduce(self.__pgfile, 'gstut')
    log.debug('Collecting information from gstut {0}'.format(self))
    self.__info(gstutpg)
    log.debug('Solving gstut {0}'.format(self))
    self.__solve(gstutpg)  
    
  def phase5(self, log):
    self.__collectResults('gstut')
    log.debug('Done {0}'.format(self))
    
class PBESCase(PGCase):
  def __init__(self):
    super(PBESCase, self).__init__()
    self.result['generation'] = {}
    self.result['generation']['tool'] = "pbes2bes"
  
  def _makePBES(self):
    raise NotImplementedError() 
    
  def _makePGfile(self, _, returnExisting):
    # Optimisation: if file exists, return the existing file instead of the 
    pgfile = self._existingTempFile('gm')
    if pgfile and returnExisting:
      return pgfile
    
    pbes = self._newTempFile('pbes')
    pbes.write(self._makePBES())
    pbes.close()
    pgfile = self._newTempFilename('gm')
    try:
      result = tools.pbes2bes('-s0', '-v', '-rjittyc', '-opgsolver', pbes.name, pgfile, memlimit=PBES2BES_MEMLIMIT, timeout=PBES2BES_TIMEOUT, timed=True)
      os.unlink(pbes.name)
    except (OutOfMemory, Timeout) as e:
      result = e.result
      
    self.result['generation']['times'] = result['times']
    self.result['generation']['memory'] = result['memory']
    
    return pgfile

