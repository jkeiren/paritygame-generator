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

class LeaderSpec(Spec):
  def mcrl2(self, nparticipants):
    return self._template.substitute(nparticipants=nparticipants)

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

__SPECS = {
    'Debug spec': Spec('debugging'),
    'ABP': DataSpec('abp'),
    'Onebit': DataSpec('onebit'),
    'BRP': DataSpec('brp'),
    'SWP': SWPSpec(),
    'IEEE1394': Spec('ieee1394'),
    'Lift (Incorrect)': LiftSpec('lift-incorrect'),
    'Lift (Correct)': LiftSpec('lift-correct'),
    'Hanoi': Spec('hanoi'),
    'Elevator': Spec('elevator'),
    'Snake': Spec('snake'),
    'Clobber': Spec('clobber'),
    'Hex': Spec('hex'),
    'Othello': Spec('othello'),
    'Leader': LeaderSpec('leader'),
    'Domineering': Spec('domineering')
  }

def get(name):
  return __SPECS[name]
