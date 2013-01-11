import string
import os.path

class Spec(object):
  TEMPLATE = None
  @property
  def _template(self):
    return string.Template(open(os.path.join(os.path.split(__file__)[0], 'mcrl2', self.TEMPLATE + '.mcrl2')).read())

class BufferSpec(Spec):
  TEMPLATE = 'buffer'
  def mcrl2(self, buffersize, datasize):
    return self._template.substitute(
      buffersize=buffersize, 
      data='|'.join(['d' + str(i) for i in range(0, datasize)]))

class SWPListsSpec(Spec):
  TEMPLATE = 'swp_lists'
  def mcrl2(self, windowsize, datasize):
    return self._template.substitute(
      windowsize=windowsize,
      data='|'.join(['d' + str(i) for i in range(0, datasize)]),
      initialwindow='[{0}]'.format(','.join(['d1'] * windowsize)),
      emptywindow='[{0}]'.format(','.join(['false'] * windowsize))
    )

__SPECS = {
    'SWP': SWPListsSpec(),
    'Buffer': BufferSpec()    
  }

def get(name):
  return __SPECS[name]