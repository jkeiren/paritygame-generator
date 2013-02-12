import multiprocessing
import logging
import traceback
import tempfile
import os
import re
import tools
import pool
import sys
from tools import OutOfMemory, Timeout

TIMEOUT = 12*60*60 # 12 hours for getting info
LPSTOOLS_TIMEOUT = TIMEOUT
MLSOLVER_TIMEOUT= 60*60
PBES2BES_TIMEOUT = TIMEOUT
PGINFO_TIMEOUT = TIMEOUT
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

class PGCase(TempObj):
  def __init__(self):
    super(PGCase, self).__init__()
    self.result = {}
    self.result['pginfo'] = None
    self.result['yamlfile'] = None
    self.__solvepg = None
    self.__solvebes = None

  def _makePGfile(self, log, overwriteExisting):
    raise NotImplementedError()

  def __collectInfo(self, pgfile):
    '''Gather information from the parity game.'''
    if RETURN_EXISTING:
      self.result['yamlfile'] = self._name("yaml")
      if os.path.exists(self.result['yamlfile']) and os.path.getsize(self.result['yamlfile']) > 0:
          self.result['yamlfile'] = self._newTempFilename("yaml")
    else:
      self.result['yamlfile'] = self._newTempFilename("yaml")

    try:
      result = tools.pginfo('-v', '-m', '30000', '-n', '2', pgfile, self.result['yamlfile'], memlimit=PGINFO_MEMLIMIT, timeout=PGINFO_TIMEOUT, timed=True)
    except (Timeout, OutOfMemory):
      # Handle gracefully, recording the output using the normal ways
      pass
    self.result['pginfo'] = cleanResult(result)

  def phase0(self, log):
    self.__pgfile = self._makePGfile(log, RETURN_EXISTING)
    log.debug('Collecting information from {0}'.format(self))
    self.__collectInfo(self.__pgfile)
      
class PBESCase(PGCase):
  def __init__(self):
    super(PBESCase, self).__init__()
  
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
    result = tools.pbes2bes('-s0', '-v', '-rjittyc', '-opgsolver', pbes.name, pgfile, memlimit=PBES2BES_MEMLIMIT, timeout=PBES2BES_TIMEOUT, timed=True)
    self.result['pbes2bes'] = cleanResult(result)
    os.unlink(pbes.name)
    return pgfile

