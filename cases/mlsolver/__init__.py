from cases import tools, TempObj, PGCase
import formulas
import os

class Case(PGCase):
  def __init__(self, name, **kwargs):
    super(Case, self).__init__()
    self.formula = formulas.get(name)
    self.__name = name
    self.__kwargs = kwargs
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = '{0}{1}'.format(self.__name, ('_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items())))
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '')
  
  def _makePGfile(self, _, returnExisting):
    pgfile = self._existingTempFile('gm')
    if pgfile and returnExisting:
      return pgfile
    
    pgfilename = self._newTempFilename('gm')
    pg = tools.mlsolver('-ve', '--{0}'.format(self.formula.mode()), self.formula.type(), '-pg', self.formula.form(**self.__kwargs))
    pgfile = open(pgfilename, 'w')
    pgfile.write(pg)
    pgfile.close()
    return pgfilename

def getcases():
  return \
    [Case('Include', n=2)] +\
    [Case('Nester', n=2)] + \
    [Case('StarNester', k=i,n=2) for i in range(1,4)] + \
    [Case('Petri', n=2)] + \
    [Case('ParityAndBuechi', n=2)] + \
    [Case('MuCalcLimitClosure', n=0,phi="p")] + \
    [Case('CTLLimitClosure', phi="p")] + \
    [Case('CTLStarLimitClosure', phi="G(~q_1)", psi="q_3 & X q_2")] + \
    [Case('CTLStarSimpleLimitClosure', phi="q_3 & X q_2")] + \
    [Case('DemriKillerFormula', n=2)] + \
    [Case('FairScheduler', n=2)] + \
    [Case('LTMucalcBinaryCounter', n=2)] + \
    [Case('CTLStarBinaryCounter', n=2)] + \
    [Case('PDLBinaryCounter', n=2)] + \
    [Case('HugeModels', n=1)]

