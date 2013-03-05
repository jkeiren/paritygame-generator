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

class DataSpec(Spec):
  def __init__(self, template):
    super(DataSpec, self).__init__(template)
  
  def mcrl2(self, datasize):
    return self._template.substitute(
      data='|'.join(['d' + str(i) for i in range(0, datasize)])
    )

# Class to denote a mix of buffer implementations. We combine all of these,
# because lpsbisim2pbes requires shared data specifications, hence we always
# need to initialise all relevant data
class GeneralBufferSpec(Spec):
  def __init__(self, template):
    super(GeneralBufferSpec, self).__init__(template)
  
  def mcrl2(self, windowsize, capacity, datasize):
    return self._template.substitute(
      windowsize=windowsize,
      data='|'.join(['d' + str(i) for i in range(0, datasize)]),
      initialwindow='[{0}]'.format(','.join(['d1'] * windowsize)),
      emptywindow='[{0}]'.format(','.join(['false'] * windowsize)),
      capacity=capacity
    )
  
__SPECS = {
    'Buffer': GeneralBufferSpec('buffer'),
    'ABP': GeneralBufferSpec('abp'),
    'ABP(BW)': GeneralBufferSpec('abp_bw'),
    'CABP': GeneralBufferSpec('cabp'),
    'Onebit': GeneralBufferSpec('onebit'),
    'Par': GeneralBufferSpec('par'),    
    'SWP': GeneralBufferSpec('swp_lists'),
    'Hesselink (Specification)': DataSpec('hesselink_spec'),
    'Hesselink (Implementation)': DataSpec('hesselink')
  }

def get(name):
  return __SPECS[name]
