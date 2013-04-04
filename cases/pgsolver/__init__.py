import os
from cases import PGCase, tools, PGSOLVER_MEMLIMIT, PGSOLVER_TIMEOUT, Timeout, OutOfMemory

class Case(PGCase):
  def __init__(self, generator, *args, **kwargs):
    super(Case, self).__init__()
    self.__generator = generator
    self.__args = [str(x) for x in args]
    self.__kwargs = kwargs
    self._prefix = '{0}({1}){2}'.format(self.__generator, ', '.join(self.__args), '_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items()))
    self._outpath = os.path.join(os.path.split(__file__)[0], 'data')
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self.result['case'] = str(self)
    self.result['generation'] = {}
    self.result['generation']['tool'] = "pgsolver"
  
  def __str__(self):
    return '{0}({1})'.format(self.__generator, ', '.join(self.__args))
  
  def _makePGfile(self, log, returnExisting):
    pgfile = self._existingTempFile('gm')
    if pgfile and returnExisting:
      return pgfile
    
    pgfile = self._newTempFile('gm')
    try:
      result = tools.Tool(self.__generator, log, memlimit=PGSOLVER_MEMLIMIT, timeout=PGSOLVER_TIMEOUT, timed=True, hastimings=False)(*self.__args)
      pgfile.write(result['out'])
      pgfile.close()
      self.result['generation']['times'] = result['times']
      self.result['generation']['memory'] = result['memory']
    except (Timeout, OutOfMemory) as e:
      self.result['generation']['times'] = e.result['times']
      self.result['generation']['memory'] = e.result['memory']
      raise e
    return pgfile.name

def getcases(debugOnly = False):
  if debugOnly:
    return [Case('elevatorverification', n) for n in range(3, 4)]
  
  # ctlstarsudokugenerator
     # elevatortsgenerator
  # jurdzinskigame
  # laddergame
  # ltmcparitybuechigenerator
  # modelcheckerladder
  # mucalcsudokugenerator
  # pdlsudokugenerator
    # philosepherstsgenerator
  # recursiveladder
  # steadygame
  nRandom = 25
  return \
    [Case('elevatorverification', n) for n in range(3, 8)] + \
    [Case('elevatorverification', '-u', n) for n in range(3, 8)] + \
    [Case('towersofhanoi', n) for n in range(5, 12)] + \
    [Case('cliquegame', n) for n in [100, 200, 500, 1000, 2000, 5000, 10000] ] + \
    [Case('jurdzinskigame', n, m) for n in [50, 100, 200, 500] for m in [50, 100, 200, 500] ] + \
    [Case('laddergame', n) for n in [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] ] + \
    [Case('modelcheckerladder', n) for n in [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] ] + \
    [Case('recursiveladder', n) for n in [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] ] + \
    [Case('randomgame', n, 10, 1, 20, id=id) for id in range(0,nRandom) for n in [1000, 5000, 10000, 20000, 50000] ] + \
    [Case('clusteredrandomgame', n, 10, 1, 50, 10, 0, 5, 1, 10, id=id) for id in range(0,nRandom) for n in [1000, 5000, 10000, 20000, 50000, 100000, 200000] ] + \
    [Case('steadygame', n, 1, 20, 1, 20, id=id) for n in [1000, 5000, 10000, 20000, 50000, 10000] for id in range(0,nRandom)]
    
    
