from cases import tools, TempObj, PGCase, MLSOLVER_TIMEOUT, MLSOLVER_MEMLIMIT
import formulas
import os

class MLSolverCase(PGCase):
  def __init__(self, name, compact, **kwargs):
    super(MLSolverCase, self).__init__()
    self.formula = formulas.get(name)
    self.__name = name
    self.__compact = compact
    self.__kwargs = kwargs
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = '{0}{1}{2}'.format(self.__name, ('_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items())), "_compact" if self.__compact else "")
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}{2}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '', " compact" if self.__compact else "")
  
  def _makePGfile(self, _, returnExisting):
    pgfile = self._existingTempFile('gm')
    if pgfile and returnExisting:
      return pgfile
    
    pgfilename = self._newTempFilename('gm')
    if self.__compact:
      pg = tools.mlsolver('-ve', '--option', 'comp', '--{0}'.format(self.formula.mode()), self.formula.type(), '-pg', self.formula.form(**self.__kwargs), timeout=MLSOLVER_TIMEOUT, memlimit=MLSOLVER_MEMLIMIT)
    else:
      pg = tools.mlsolver('-ve', '--{0}'.format(self.formula.mode()), self.formula.type(), '-pg', self.formula.form(**self.__kwargs), timeout=MLSOLVER_TIMEOUT, memlimit=MLSOLVER_MEMLIMIT)
    pgfile = open(pgfilename, 'w')
    pgfile.write(pg)
    pgfile.close()
    return pgfilename

class Case(TempObj):
  def __init__(self, name, **kwargs):
    super(Case, self).__init__()
    self.__name = name
    self.__kwargs = kwargs
    self._prefix = '{0}{1}'.format(self.__name, ('_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items())))
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '')
  
  def phase0(self, log):
    '''Generates an LPS and creates subtasks for every property that should be
    verified.'''
    
    for compact in True, False:
      self.subtasks.append(MLSolverCase(self.__name, compact, **self.__kwargs))

def getcases(debugOnly = False):
  if debugOnly:
    return []
  return \
    [Case('Include', n=n) for n in range(1,9)] + \
    [Case('Nester', n=n) for n in range(1,9)] + \
    [Case('StarNester', k=k,n=n) for k in range(1,4) for n in range(1,9)] + \
    [Case('Petri', n=n) for n in range(1,9)] + \
    [Case('ParityAndBuechi', n=n) for n in range(1,9)] + \
    [Case('MuCalcLimitClosure', n=0,phi="p")] + \
    [Case('FLCTLLimitClosure', n=n) for n in range(1,9)] + \
    [Case('FLCTLStarLimitClosure', n=n) for n in range(1,5)] + \
    [Case('FLCTLStarSimpleLimitClosure', n=n) for n in range(1,9)] + \
    [Case('DemriKillerFormula', n=n) for n in range(1,4)] + \
    [Case('FairScheduler', n=n) for n in range(1,9)] + \
    [Case('LTMucalcBinaryCounter', n=n) for n in range(1,9)] + \
    [Case('CTLStarBinaryCounter', n=n) for n in range(1,9)] + \
    [Case('PDLBinaryCounter', n=n) for n in range(1,9)] + \
    [Case('HugeModels', n=n) for n in range(1,5)]

