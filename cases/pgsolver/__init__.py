import os
from cases import PGCase, tools, PGSOLVER_MEMLIMIT, PGSOLVER_TIMEOUT

class Case(PGCase):
  def __init__(self, generator, *args):
    super(Case, self).__init__()
    self.__generator = generator
    self.__args = [str(x) for x in args]
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
  
  def __str__(self):
    return '{0}({1})'.format(self.__generator, ', '.join(self.__args))
  
  def _makePGfile(self, log, returnExisting):
    pgfile = self._existingTempFile('gm')
    if pgfile and returnExisting:
      return pgfile
    
    pgfile = self._newTempFile('gm')
    pgfile.write(tools.Tool(self.__generator, log, memlimit=PGSOLVER_MEMLIMIT, timeout=PGSOLVER_TIMEOUT)(*self.__args))
    pgfile.close()
    return pgfile.name

def getcases(debugOnly = False):
  if debugOnly:
    return []
  return \
    [Case('elevatorverification', n) for n in range(3, 8)] + \
    [Case('elevatorverification', '-u', n) for n in range(3, 8)] + \
    [Case('elevatorverification_alt', n) for n in range(3, 8)] + \
    [Case('elevatorverification_alt', '-u', n) for n in range(3, 8)] + \
    [Case('towersofhanoi', n) for n in range(5, 12)] + \
    [Case('towersofhanoi_alt', n) for n in range(5, 12)]
