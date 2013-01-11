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

class TempObj(pool.Task):
  def __init__(self):
    super(TempObj, self).__init__()
    self._temppath = '.'
    self._prefix = ""

  def __escape(self, s):
    return s.replace('/', '_').replace(' ', '_')
    
  def _newTempFile(self, ext, extraprefix=""):
    if not os.path.exists(self._temppath):
      os.makedirs(self._temppath)
    name = self._temppath + '/' + self.__escape(self._prefix) + extraprefix + '.' + ext
    if self._prefix <> "" and not os.path.exists(name):
      fn = open(name, 'w+b')
      return fn
    else:
      return tempfile.NamedTemporaryFile(dir=self._temppath, prefix=self.__escape(self._prefix)+extraprefix, suffix='.'+ext, delete=False)
    
  def _newTempFilename(self, ext, extraprefix=""):
    fn = self._newTempFile(ext, extraprefix)
    fn.close()
    return fn.name

class SolveTask(pool.Task):
  def __init__(self, name, filename, *args):
    super(SolveTask, self).__init__()
    self.__pgfile = filename
    self.__opts = list(args)
    self.name = name
    self.time = 'error'
    self.size = 'error'
    self.result = None
  
  def run(self, log):
    if self.name.startswith('pbespgsolve'):
      self.run_pbespgsolve(log)
    else:
      self.run_pgsolver(log)
  
  def run_pbespgsolve(self, log):
    try:      
      result, t = tools.pbespgsolve(self.__pgfile, *self.__opts, timed=True, timeout=SOLVE_TIMEOUT)
      self.time = t[0]['timing']['solving']      
      self.result = result.strip()
    except tools.Timeout:
      log.info('Timeout')
      self.time = 'timeout'
      self.result = 'unknown'
  
  def run_pgsolver(self, log):
    try:
      opts = self.__opts + ['-v', '2', self.__pgfile]
      out = tools.pgsolver(*opts, timeout=SOLVE_TIMEOUT)
      self.time = re.search('Overall\s*\|.*?\s+([0-9.]+) sec', out, re.DOTALL).group(1)
      self.result = re.search('Player (0|1) wins from nodes:[^}]*?[{,]0[,}]', out, re.DOTALL).group(1)
      self.result = 'true' if self.result == '0' else 'false'
    except tools.Timeout as ex:
      log.info('Timeout')
      self.time = 'timeout'    
      self.result = 'unknown'  

class PGCase(TempObj):
  def __init__(self):
    super(PGCase, self).__init__()
    self.sizes = {}
    self.times = {}
    self.solutions = {}
    self.__solvepg = None
    self.__solvebes = None

  def _makePGfile(self, log):
    raise NotImplementedError()

  def __reduce(self, pgfile, equiv):
    '''Reduce the PG modulo equiv using pgconvert.'''
    reduced = self._newTempFilename('gm')
    result, timing, sizes = tools.pgconvert('-ve{0}'.format(equiv), pgfile, reduced, timed=True)
    self.sizes['orig'] = {'vertices': sizes['vorig'], 'edges': sizes['eorig']}
    self.sizes[equiv] = {'vertices': sizes['vred'], 'edges': sizes['ered']}
    self.times.setdefault(equiv, {})['reduction'] = timing[0]['timing']['reduction']
    return reduced
  
  def __solve(self, pgfile):
    '''Solve besfile using pbsespgsolve and pgsolver.'''
    self.subtasks = [
      SolveTask('pbespgsolve (spm)', pgfile),
      SolveTask('pbespgsolve (recursive)', pgfile, '-srecursive'),
#      SolveTask('pgsolver (optimized spm)', pgfile, '-sp'),
      SolveTask('pgsolver (optimized recursive)', pgfile, '-re'),
      SolveTask('pgsolver (optimized bigstep)', pgfile, '-bs'),
#      SolveTask('pgsolver (optimized strategy improvement)', pgfile, '-si'),
#      SolveTask('pgsolver (unoptimized spm)', pgfile, '-sp', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized recursive)', pgfile, '-re', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized bigstep)', pgfile, '-bs', '-dgo', '-dsg', '-dlo'),
#      SolveTask('pgsolver (unoptimized strategy improvement)', pgfile, '-si', '-dgo', '-dsg', '-dlo')
    ]
  
  def __collectResults(self, name):
    for task in self.results:
      self.times.setdefault(name, {})[task.name] = task.time
      self.solutions.setdefault(name, {})[task.name] = task.result
  
  def phase0(self, log):
    self.__pgfile = self._makePGfile(log)
    log.debug('Solving original ({0})'.format(self))
    self.__solve(self.__pgfile)
    
  def phase1(self, log):
    self.__collectResults('orig')
    log.debug('Reducing original modulo stut ({0})'.format(self))
    self._prefix = self._prefix + '_stut'
    stutpg = self.__reduce(self.__pgfile, 'stut')
    log.debug('Solving stut ({0})'.format(self))
    self.__solve(stutpg)
    
  def phase2(self, log):
    self.__collectResults('stut')
    log.debug('Reducing original modulo gstut ({0})'.format(self))
    self._prefix = self._prefix.replace('_stut', '_gstut')
    gstutpg = self.__reduce(self.__pgfile, 'gstut')
    log.debug('Solving stut for ({0})'.format(self))
    self.__solve(gstutpg)

  def phase3(self, log):
    self.__collectResults('gstut')
    log.debug('Done ({0})'.format(self))

class PBESCase(PGCase):
  
  def _makePBES(self):
    raise NotImplementedError() 
    
  def _makePGfile(self, _):
    pbes = self._newTempFile('pbes')
    pbes.write(self._makePBES())
    pbes.close()
    pgfile = self._newTempFilename('gm')
    tools.pbes2bes('-s0', '-v', '-rjittyc', '-opgsolver', pbes.name, pgfile)
    os.unlink(pbes.name)
    return pgfile

