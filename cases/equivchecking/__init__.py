import tempfile
import logging
import traceback
import multiprocessing
import os
from cases import tools, PBESCase, TempObj, LPSTOOLS_MEMLIMIT, LPSTOOLS_TIMEOUT
import specs

class EquivCase(PBESCase):
  def __init__(self, description, lpsfile1, lpsfile2, equiv, temppath):
    super(EquivCase, self).__init__()
    self.__desc = description
    self._temppath = temppath
    self._prefix = self.__desc + "eq=%s" % (equiv)
    self.lpsfile1 = lpsfile1
    self.lpsfile2 = lpsfile2
    self.equiv = equiv
    self.result['equivalence'] = str(self)
    
  def __str__(self):
    return self.equiv
  
  def _makePBES(self):
    result = tools.lpsbisim2pbes('-b' + self.equiv, self.lpsfile1, self.lpsfile2, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    result = tools.pbesconstelm(stdin=result['out'], memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    return result['out']
  
class Case(TempObj):
  def __init__(self, description, spec1, spec2):
    super(Case, self).__init__()
    self.__desc = description
    self.__files = []
    self._outdir = os.path.join(os.path.split(__file__)[0], 'data')
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = self.__desc
    self.spec1 = spec1
    self.spec2 = spec2
    self.result = {}
    self.result['case'] = str(self)
    self.result['instances'] = []
  
  def __str__(self):
    return self.__desc

  def __linearise(self, log):
    '''Linearises self.spec1 and self.spec2 and applies lpssuminst to the 
       resulting LPSs.'''
    log.info('Linearising LPSs for {0}'.format(self))
    result1 = tools.mcrl22lps('-fnD', stdin=self.spec1, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    result2 = tools.mcrl22lps('-fnD', stdin=self.spec2, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.info('Applying lpssuminst to LPSs for {0}'.format(self))
    result1 = tools.lpssuminst('-f', stdin=result1['out'], memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    result2 = tools.lpssuminst('-f', stdin=result2['out'], memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    lpsfile1 = self._newTempFile('lps')
    lpsfile1.write(result1['out'])
    lpsfile1.close()
    lpsfile2 = self._newTempFile('lps')
    lpsfile2.write(result2['out'])
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
    for r in self.results:
      self.result['instances'].append(r.result)

class SameParamCase(Case):
  def __init__(self, name1, name2, **kwargs):
    super(SameParamCase, self).__init__(
      '{0}/{1} ({2})'.format(name1, name2, ' '.join('{0}={1}'.format(k,v) for k,v in kwargs.items())),
      specs.get(name1).mcrl2(**kwargs),
      specs.get(name2).mcrl2(**kwargs))
  
  
def getcases(debugOnly = False):
  if debugOnly:
    return \
      [SameParamCase('Buffer', 'ABP', windowsize=1, capacity=1, datasize=2)]
     
  else:
    return \
      [SameParamCase('ABP', 'ABP(BW)', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('ABP(BW)', 'CABP', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('ABP', 'CABP', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'ABP', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'ABP(BW)', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'CABP', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'Par', windowsize=1, capacity=1, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'Onebit', windowsize=1, capacity=2, datasize=d) for d in range(2,5)] + \
      [SameParamCase('Buffer', 'SWP', windowsize=1, capacity=2, datasize=d) for d in range(2,5)] + \
      [SameParamCase('ABP', 'ABP', windowsize=1, capacity=1, datasize=d) for d in range(2,9)] + \
      [SameParamCase('Hesselink (Specification)', 'Hesselink (Implementation', datasize=d) for d in range(2,6)]
      