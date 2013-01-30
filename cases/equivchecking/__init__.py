import tempfile
import logging
import traceback
import multiprocessing
import os
from cases import tools, PBESCase, TempObj, MEMLIMIT, LPSTOOLS_MEMLIMIT

class EquivCase(PBESCase):
  def __init__(self, description, lpsfile1, lpsfile2, equiv, temppath):
    super(EquivCase, self).__init__()
    self.__desc = description
    self._temppath = temppath
    self._prefix = self.__desc + "eq=%s" % (equiv)
    self.lpsfile1 = lpsfile1
    self.lpsfile2 = lpsfile2
    self.equiv = equiv
    
  def __str__(self):
    return self.equiv
  
  def _makePBES(self):
    pbes = tools.lpsbisim2pbes('-b' + self.equiv, self.lpsfile1, self.lpsfile2, memlimit=LPSTOOLS_MEMLIMIT)
    return tools.pbesconstelm(stdin=pbes, memlimit=LPSTOOLS_MEMLIMIT)
  
class Case(TempObj):
  def __init__(self, description, spec1, spec2):
    super(Case, self).__init__()
    self.__desc = description
    self.__files = []
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = self.__desc
    self.spec1 = spec1
    self.spec2 = spec2
    self.sizes = {}
    self.times = {}
    self.solutions = {}
  
  def __str__(self):
    return self.__desc

  def __linearise(self, log):
    '''Linearises self.spec1 and self.spec2 and applies lpssuminst to the 
       resulting LPSs.'''
    log.info('Linearising LPSs for {0}'.format(self))
    lps1 = tools.mcrl22lps('-fnD', stdin=self.spec1, memlimit=LPSTOOLS_MEMLIMIT)
    lps2 = tools.mcrl22lps('-fnD', stdin=self.spec2, memlimit=LPSTOOLS_MEMLIMIT)
    log.info('Applying lpssuminst to LPSs for {0}'.format(self))
    lps1 = tools.lpssuminst('-f', stdin=lps1, memlimit=LPSTOOLS_MEMLIMIT)
    lps2 = tools.lpssuminst('-f', stdin=lps2, memlimit=LPSTOOLS_MEMLIMIT)
    lpsfile1 = self._newTempFile('lps')
    lpsfile1.write(lps1)
    lpsfile1.close()
    lpsfile2 = self._newTempFile('lps')
    lpsfile2.write(lps2)
    lpsfile2.close()
    return lpsfile1.name, lpsfile2.name
  
  def phase0(self, log):
    lpsfile1, lpsfile2 = self.__linearise(log)
    for equiv in ['strong-bisim', 'weak-bisim', 'branching-bisim', 'branching-sim']:
      self.subtasks.append(EquivCase(self.__desc, lpsfile1, lpsfile2, equiv, self._temppath))
    self.__files = [lpsfile1, lpsfile2]
  
  def phase1(self, log):
    log.info('Finalising {0}'.format(self))
    for filename in self.__files:
      os.unlink(filename)
  
def getcases():
  import specs
  buf = specs.get('Buffer')
  swp = specs.get('SWP')
  return \
    [Case('Buffer/SWP (w={0}, d={1})'.format(w, d), swp.mcrl2(w, d), buf.mcrl2(2 * w, d))
     for w, d in [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 2), (2, 3)]]
