import multiprocessing
import logging
import traceback
import tempfile
import os
import re
import tools
import pool
import sys

SOLVE_TIMEOUT = 3600
RETURN_EXISTING = True

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
    self.sizes = {}
    self.times = {}
    self.solutions = {}
    self.__solvepg = None
    self.__solvebes = None

  def _makePGfile(self, log, overwriteExisting):
    raise NotImplementedError()

  def __collectInfo(self, pgfile):
    '''Reduce the PG modulo equiv using pgconvert.'''
    global RETURN_EXISTING
    
    if RETURN_EXISTING:
      yamlfile = self._name("yaml")
      if os.path.exists(yamlfile) and os.path.getsize(yamlfile) > 0:
          yamlfile = self._newTempFilename("yaml")
    else:
      yamlfile = self._newTempFilename("yaml")

    tools.pginfo('-v', '-m', '30000', '-n', '2', pgfile, yamlfile)
    return yamlfile

  def phase0(self, log):
    global RETURN_EXISTING
    self.__pgfile = self._makePGfile(log, RETURN_EXISTING)
    log.debug('Collecting information from {0}'.format(self))
    self.__collectInfo(self.__pgfile)
    
class PBESCase(PGCase):
  
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
    tools.pbes2bes('-s0', '-v', '-rjittyc', '-opgsolver', pbes.name, pgfile)
    os.unlink(pbes.name)
    return pgfile

