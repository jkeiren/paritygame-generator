from cases import tools, TempObj, PBESCase, LPSTOOLS_MEMLIMIT, LPSTOOLS_TIMEOUT
import specs
import os.path
import logging
import tempfile
import re
import sys
import multiprocessing
import traceback

class Property(PBESCase):
  def __init__(self, description, lps, mcf, temppath):
    PBESCase.__init__(self)
    self.__desc = description
    self._temppath = temppath
    self._prefix = self.__desc + '_' + os.path.splitext(os.path.split(mcf)[1])[0]
    self.lps = lps
    self.mcffile = mcf
    self.renfile = os.path.splitext(self.mcffile)[0] + '.ren'
  
  def __str__(self):
    return os.path.splitext(os.path.split(self.mcffile)[1])[0]
  
  def __rename(self):
    '''If a lpsactionrename specification exists for this property, transform
       the LPS.'''
    if os.path.exists(self.renfile):
      self.lps = tools.lpsactionrename('-f', self.renfile, '-v', stdin=self.lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
  
  def _makePBES(self):
    '''Generate a PBES out of self.lps and self.mcffile, and apply pbesconstelm
       to it.'''
    self.__rename()
    return tools.pbesconstelm('-v', stdin=tools.lps2pbes('-f', self.mcffile, '-v', stdin=self.lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT))

class Case(TempObj):
  def __init__(self, name, **kwargs):
    TempObj.__init__(self)
    spec = specs.get(name)
    self.__name = name
    self.__kwargs = kwargs
    self._mcrl2 = spec.mcrl2(**kwargs)
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = '{0}{1}'.format(self.__name, ('_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items())))
    self.proppath = os.path.join(os.path.split(__file__)[0], 'properties', spec.TEMPLATE)
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '')

  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2.'''
    log.debug('Linearising {0}'.format(self))
    return tools.mcrl22lps('-fvD', stdin=self._mcrl2, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)

  def phase0(self, log):
    '''Generates an LPS and creates subtasks for every property that should be
    verified.'''
    lps = self._makeLPS(log)    
    for prop in os.listdir(self.proppath):
      if not prop.endswith('.mcf'):
        continue
      self.subtasks.append(Property(self._prefix, lps, os.path.join(self.proppath, prop), 
                                    self._temppath))
    
class IEEECase(Case):
  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2 and applies lpssuminst to the
    result.'''
    log.debug('Linearising {0}'.format(self))
    lps = tools.mcrl22lps('-vD', stdin=self._mcrl2, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.debug('Applying suminst on LPS of {0}'.format(self))
    return tools.lpssuminst(stdin=lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)

class GameCase(Case):
  def __init__(self, name, boardsize=4, use_compiled_constelm=False, **kwargs):
    super(GameCase, self).__init__(name, **kwargs)
    self.__boardsize = boardsize
    self.__use_compiled_constelm = use_compiled_constelm
  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2 and applies lpssuminst,
    lpsparunfold and lpsconstelm to the result.'''
    log.debug('Linearising {0}'.format(self))
    lps = tools.mcrl22lps('-vfD', stdin=self._mcrl2, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.debug('Applying suminst on LPS of {0}'.format(self))
    lps = tools.lpssuminst(stdin=lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.debug('Applying parunfold (for Board) on LPS of {0}'.format(self))
    lps = tools.lpsparunfold('-lv', '-n{0}'.format(self.__boardsize), '-sBoard', stdin=lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.debug('Applying parunfold (for Row) on LPS of {0}'.format(self))
    lps = tools.lpsparunfold('-lv', '-n{0}'.format(self.__boardsize), '-sRow', stdin=lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)
    log.debug('Applying constelm on LPS of {0}'.format(self))
    return tools.lpsconstelm('-ctvrjittyc' if self.__use_compiled_constelm else '-ctv', stdin=lps, memlimit=LPSTOOLS_MEMLIMIT, timeout=LPSTOOLS_TIMEOUT)

def getcases(debugOnly = False):
  if(debugOnly):
    return [Case('Debug spec'),
            IEEECase('IEEE1394')]
  
  return \
    [Case('Debug spec'),
     Case('Othello'),
     GameCase('Clobber'),
     GameCase('Snake'),
     GameCase('Hex'),
     GameCase('Domineering', boardsize=5),
     Case('Elevator'),
     Case('Hanoi'),
     IEEECase('IEEE1394')] + \
    [Case('Lift (Correct)', nlifts=n) for n in range(2, 5)] + \
    [Case('Lift (Incorrect)', nlifts=n) for n in range(2, 5)] + \
    [Case('ABP', datasize=i) for i in [2,4,8,16,32]] + \
    [Case('Onebit', datasize=i) for i in range(2,7)] + \
    [Case('BRP', datasize=i) for i in range(2,7)] + \
    [Case('SWP', windowsize=1, datasize=i) for i in range(2, 7)] + \
    [Case('SWP', windowsize=2, datasize=i) for i in range(2, 7)] + \
    [Case('SWP', windowsize=3, datasize=i) for i in range(2, 5)] + \
    [Case('SWP', windowsize=4, datasize=2)] + \
    [Case('Leader', nparticipants=n) for n in range(3, 7)]
