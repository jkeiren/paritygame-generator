import subprocess
import logging
import tempfile
import threading
import yaml
import os
import re
import resource

__LOG = logging.getLogger('tools')

class ToolException(Exception):
  def __init__(self, tool, exitcode, out, err):
    Exception.__init__(self)
    self.__out = out
    self.__err = err
    self.__ret = exitcode
    self.__cmdline = ' '.join(tool)
  
  def __str__(self):
    return 'The commandline "{0}" failed with exit code "{1}".\nStandard error:\n{2}\nStandard output:\n{3}\n'.format(
      self.__cmdline, self.__ret, self.__err, self.__out)

class Timeout(Exception):
  def __init__(self, out, err):
    super(Timeout, self).__init__()
    self.out = out
    self.err = err
    
class MemoryLimitExceeded(Exception):
  def __init__(self, tool, out, err):
    Exception.__init__(self)
    self.__out = out
    self.__err = err
    self.__cmdline = ' '.join(tool)

  def __str__(self):
    return 'The commandline "{0}" failed with an out of memory error.\nStandard error:\n{1}\nStandard output:\n{2}\n'.format(
      self.__cmdline, self.__err, self.__out)

def setlimits(memlimit):
  if memlimit != None:
    resource.setrlimit(resource.RLIMIT_AS, (memlimit,memlimit))

class Tool(object):
  def __init__(self, name, log, filter_=None, timed=False, timeout=None, memlimit=None):
    self.__name = name
    self.__log = log
    self.__timeout = timeout
    self.__memlimit = memlimit 
    self.__filter = filter_
    self.__timed = timed
    self.result = None
    self.error = None
    
  def __run(self, stdin, stdout, stderr, timeout, memlimit, *args):
    cmdline = []
    cmdline += [self.__name] + [str(x) for x in args]
    self.__log.info('Running {0}'.format(' '.join(cmdline)))
    try:
      p = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=stdout, 
                           stderr=stderr, preexec_fn=setlimits(memlimit))
      if timeout is not None:
        timer = threading.Timer(timeout, p.kill)
        timer.start()
        self.result, self.error = p.communicate(stdin)
        if not timer.isAlive():
          raise Timeout(self.result, self.error)
        else: 
          timer.cancel()
      else:
        self.result, self.error = p.communicate(stdin)
      
      if p.returncode != 0:
        raise ToolException(cmdline, p.returncode, self.result, self.error)
           
    except (ToolException, Timeout) as e:
      raise e
    except:
      raise MemoryLimitExceeded(cmdline, self.result, self.error) 
  
  def __run_timed(self, stdin, stdout, stderr, timeout, memlimit, *args):
    timings = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
    timings.close()
    self.__run(stdin, stdout, stderr, timeout, memlimit, '--timings='+timings.name, *args)
    t = yaml.load(open(timings.name).read())
    os.unlink(timings.name)
    self.result = [self.result, t]
  
  def __apply_filter(self, filter_):
    m = re.search(filter_, self.error, re.DOTALL)
    if m is not None:
      if isinstance(self.result, list):
        self.result.append(m.groupdict())
      else:
        self.result = [self.result, m.groupdict()]
    else:
      self.__log.error('No match!')
      self.__log.error(filter_)
      self.__log.error(self.error)
      if isinstance(self.result, list):
        self.result.append({})
      else:
        self.result = [self.result, {}]
  
  def __str__(self):
    return self.__name
  
  def __call__(self, *args, **kwargs):
    stdin = kwargs.pop('stdin', None)
    stdout = kwargs.pop('stdout', subprocess.PIPE)
    stderr = kwargs.pop('stderr', subprocess.PIPE)
    filter_ = kwargs.pop('filter', self.__filter)
    timeout = kwargs.pop('timeout', self.__timeout)
    memlimit = kwargs.pop('memlimit', self.__memlimit)
    timed = kwargs.pop('timed', self.__timed)
    if kwargs:
      raise TypeError('Unknown parameter(s) for Tool instance: ' + 
                      ', '.join(['{0}={1}'.format(k, v) 
                                 for k, v in kwargs.items()]))
    if timed:
      self.__run_timed(stdin, stdout, stderr, timeout, memlimit, *args)
    else:
      self.__run(stdin, stdout, stderr, timeout, memlimit, *args)
    self.__log.debug(self.error)
    if filter_:
      self.__apply_filter(filter_)
    return self.result

pginfo = Tool('pginfo', __LOG)
mcrl22lps = Tool('mcrl22lps', __LOG)
lps2pbes = Tool('lps2pbes', __LOG)
lpsactionrename = Tool('lpsactionrename', __LOG)
lpssuminst = Tool('lpssuminst', __LOG)
lpsparunfold = Tool('lpsparunfold', __LOG)
lpsconstelm = Tool('lpsconstelm', __LOG)
pbesparelm = Tool('pbesparelm', __LOG)
pbesconstelm = Tool('pbesconstelm', __LOG)
pbes2bes = Tool('pbes2bes', __LOG)
pbespgsolve = Tool('pbespgsolve', __LOG)
besconvert = Tool('besconvert', __LOG)
bestranslate = Tool('bestranslate', __LOG)
ltsinfo = Tool('ltsinfo', __LOG)
pgsolver = Tool('pgsolver', __LOG)
mlsolver = Tool('mlsolver', __LOG)
PGCONVERT_RE = 'Parity game contains (?P<vorig>\d+) nodes and (?P<eorig>\d+) edges\..*?Parity game contains (?P<vred>\d+) nodes and (?P<ered>\d+) edges after[^[]*$'
pgconvert = Tool('pgconvert', __LOG, filter_=PGCONVERT_RE)
transformer = Tool('transformer', __LOG)
LTSMIN_RE = 'original LTS has (?P<V>\d+) .*? (?P<E>\d+) .*?' \
  '(?:marking divergences took .*? (?P<ptimeu>\d+.\d+) user (?P<ptimes>\d+.\d+) sys.*?)?' \
  'reduction took .*? (?P<rtimeu>\d+.\d+) user (?P<rtimes>\d+.\d+) sys.*?' \
  'reduced LTS has (?P<Vr>\d+) .*? (?P<Er>\d+)'
ltsmin = Tool('ltsmin', __LOG, filter_=LTSMIN_RE)
lpsbisim2pbes = Tool('lpsbisim2pbes', __LOG)
towersofhanoi = Tool('towersofhanoi', __LOG)
towersofhanoi_alt = Tool('towersofhanoi_alt', __LOG)
elevatorverification = Tool('elevatorverification', __LOG)
elevatorverification_alt = Tool('elevatorverification_alt', __LOG)
