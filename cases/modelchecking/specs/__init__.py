import string
import os.path

class Spec(object):
  def __init__(self, template=None):
    self.TEMPLATE = template
    if self.TEMPLATE is None:
      self.TEMPLATE = self.__class__.TEMPLATE
  @property
  def _template(self):
    return string.Template(open(os.path.join(os.path.split(__file__)[0], 'mcrl2', self.TEMPLATE + '.mcrl2')).read())
  def mcrl2(self):
    return self._template.substitute()

class LiftSpec(Spec):
  def mcrl2(self, nlifts):
    return self._template.substitute(
      nlifts=nlifts,
      lifts=' || '.join(['Lift0({0})'.format(i + 1) for i in range(0, nlifts)]))

class ElevatorSpec(Spec):
  def mcrl2(self, policy, storeys):
    return self._template.substitute(policy=policy, storeys=storeys)

class LeaderSpec(Spec):
  def mcrl2(self, nparticipants):
    return self._template.substitute(nparticipants=nparticipants,
                                     parts=' || '.join(['Part({0})'.format (i+1) for i in range(0, nparticipants)]))

class DataSpec(Spec):
  def __init__(self, template=None):
    super(DataSpec,self).__init__(template)
  
  def mcrl2(self, datasize):
    return self._template.substitute(
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)])
    )

class SWPSpec(Spec):
  TEMPLATE = 'swp'
  def mcrl2(self, windowsize, datasize):
    return self._template.substitute(
      windowsize=windowsize,
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)]),
      initialwindow='[{0}]'.format(','.join(['d1'] * windowsize)),
      emptywindow='[{0}]'.format(','.join(['false'] * windowsize))
    )
    
class HanoiSpec(Spec):
  TEMPLATE = 'hanoi'
  def mcrl2(self, ndisks):
    return self._template.substitute(ndisks=ndisks)
  
class IEEE1394Spec(Spec):
  TEMPLATE = 'ieee1394'
  def mcrl2(self, nparties, datasize, headersize, acksize):
    return self._template.substitute(
      nparties=nparties,
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)]),
      headers='|'.join(['h' + str(i + 1) for i in range(0, headersize)]),
      acks='|'.join(['a' + str(i + 1) for i in range(0, acksize)]),
      links=' || '.join(['LINK(N,{0})'.format(n) for n in range(0,nparties)])
    )
    
class BoardSpec(Spec):
  def __init__(self, template=None):
    super(BoardSpec,self).__init__(template)
  
  def mcrl2(self, width, height):
    return self._template.substitute(
      width=width,
      height=height
    )

class OthelloSpec(BoardSpec):
  def __init__(self, template=None):
    super(OthelloSpec,self).__init__(template)
  
  def mcrl2(self, width, height):
    assert(width % 2 == 0)
    assert(width >= 4)
    assert(height % 2 == 0)
    assert(height >= 4)
    
    return self._template.substitute(
      extrarows = int((height-2/2)),
      extracolumns = int((width-2/2))
    )


__SPECS = {
    'ABP': DataSpec('abp'),
    'ABP(BW)': DataSpec('abp_bw'),
    'BRP': DataSpec('brp'),
    'CABP': DataSpec('cabp'),
    'CCP': Spec('ccp33'),
    'Clobber': BoardSpec('clobber'),
    'Debug spec': Spec('debugging'),
    'Domineering': BoardSpec('domineering'),
    'Elevator': ElevatorSpec('elevator'),
    'Hanoi': HanoiSpec('hanoi'),
    'Hesselink': DataSpec('hesselink'),
    'Hex': BoardSpec('hex'),
    'IEEE1394': IEEE1394Spec(),
    'Leader': LeaderSpec('leader'),
    'Lift (Correct)': LiftSpec('lift-correct'),
    'Lift (Incorrect)': LiftSpec('lift-incorrect'),
    'Onebit': DataSpec('onebit'),
    'Othello': OthelloSpec('othello'),
    'Par': DataSpec('par'),
    'Snake': BoardSpec('snake'),
    'SWP': SWPSpec()    
  }

def get(name):
  return __SPECS[name]
