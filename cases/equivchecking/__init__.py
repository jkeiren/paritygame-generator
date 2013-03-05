import tempfile
import logging
import traceback
import multiprocessing
import os
from cases import tools, PBESCase, TempObj, LPSTOOLS_MEMLIMIT, LPSTOOLS_TIMEOUT

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
  
def getcases(debugOnly = False):
  import specs
  buf = specs.get('Buffer')
  abp = specs.get('ABP')
  abp_bw = specs.get('ABP(BW)')
  cabp = specs.get('CABP')
  par = specs.get('Par')
  onebit = specs.get('Onebit')
  swp = specs.get('SWP')
  hesselink_spec = specs.get('Hesselink (Specification)')
  hesselink = specs.get('Hesselink (Implementation)')
  if debugOnly:
    return \
      [Case('Buffer/ABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]]
  else:
    return \
      [Case('ABP/ABP(BW) (d={2})'.format(w,c,d), abp.mcrl2(w,c,d), abp_bw.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in [2, 3, 4] ]] + \
      [Case('ABP(BW)/CABP (d={2})'.format(w,c,d), abp_bw.mcrl2(w,c,d), cabp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in [2, 3, 4] ]] + \
      [Case('ABP/CABP (d={2})'.format(w,c,d), abp.mcrl2(w,c,d), cabp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in [2, 3, 4] ]] + \
      [Case('Buffer/ABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/ABP(BW) (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp_bw.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/CABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), cabp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Par (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), par.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Onebit (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), onebit.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]] + \
      [Case('ABP/ABP (d={2})'.format(w,c,d), abp.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in [2, 3, 4, 5, 6, 7, 8] ] ]