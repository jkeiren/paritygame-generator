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
  
  def _newTempFile(self, ext, extraprefix=""):
    if not os.path.exists(self._temppath):
      os.makedirs(self._temppath)
    name = self._name(ext, extraprefix)
    if self._prefix <> "" and not os.path.exists(name):
      fn = open(name, 'w+b')
      return fn
    else:
      return tempfile.NamedTemporaryFile(dir=self._temppath, prefix=self.__escape(self._prefix)+extraprefix, suffix='.'+ext, delete=False)
    
  def _newTempFilename(self, ext, extraprefix=""):
    fn = self._newTempFile(ext, extraprefix)
    fn.close()
    return fn.name
  
class PGInfoJob(TempObj):
  def __init__(self, pgfile, option):
    super(PGInfoJob, self).__init__()
    self.__pgfile = pgfile
    self.__option = option
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self.result = {}
    self.result['pginfo'] = None
    self.result['yamlfile'] = None
    self.result['option'] = self.__option
    
  def phase0(self, log):
    yamlfile = self._newTempFilename("yaml")
    try:
      result = tools.pginfo('-v', self.__pgfile, yamlfile, '--{0}'.format(self.__option), memlimit=PGINFO_MEMLIMIT, timeout=PGINFO_TIMEOUT, timed=True)
    except (Timeout, OutOfMemory) as e:
      # Handle gracefully, recording the output using the normal ways
      result = e.result
      
    self.result['pginfo'] = cleanResult(result)
    self.result['output'] = yaml.load(open(yamlfile).read())
    os.unlink(yamlfile)
  
class PGCase(TempObj):
  def __init__(self):
    super(PGCase, self).__init__()
    self.result = {}
    self.result['statistics'] = {}
    self.__solvepg = None
    self.__solvebes = None
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

  def _makePGfile(self, log, overwriteExisting):
    raise NotImplementedError()

  def phase0(self, log):
    self.__pgfile = self._makePGfile(log, RETURN_EXISTING)
    log.debug('Collecting information from {0}'.format(self))
    for opt in self.__optmap:
      self.subtasks.append(PGInfoJob(self.__pgfile, opt))
    
  def phase1(self, log):
    log.debug('Collecting results from {0}'.format(self))
    for r in self.results:
      if 'output' in r.result.keys() and r.result['output']:
        assert(len(r.result['output']) == 1)
        assert(r.result['output'].keys()[0] == self.__optmap[r.result['option']])
        (k,v) = r.result['output'].items()[0]
        
        if isinstance(v, dict):
          self.result['statistics'][k] = v
        else:
          self.result['statistics'][k] = {}
          self.result['statistics'][k]['value'] = v
      
          
        self.result['statistics'][k]['times'] = r.result['pginfo']['times']
        self.result['statistics'][k]['memory'] = r.result['pginfo']['memory']
      else: # No output recorded
        k = self.__optmap[r.result['option']]
        self.result['statistics'][k] = {}
        self.result['statistics'][k]['times'] = r.result['pginfo']['times']
        self.result['statistics'][k]['memory'] = r.result['pginfo']['memory']
        
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

