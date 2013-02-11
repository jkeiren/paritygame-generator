import subprocess
import logging
import tempfile
import threading
import yaml
import os
import re
import resource

__LOG = logging.getLogger('tools')
logging.raiseExceptions = False

_TIMEOUTSCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "timeout")

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
    
class OutOfMemory(Exception):
  def __init__(self, tool, out, err):
    super(OutOfMemory, self).__init__()
    self.__out = out
    self.__err = err

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
    timeoutcmd = []

    if timeout is not None or memlimit is not None:
      if not os.path.exists(_TIMEOUTSCRIPT):
        self.__log.error('The script {0} does not exists, cannot run without it'.format(_TIMEOUTSCRIPT))
        raise Exception('File {0} not found'.format(_TIMEOUTSCRIPT))
      
      timeoutcmd += [_TIMEOUTSCRIPT, '--confess', '--no-info-on-success']
      if timeout is not None:
        timeoutcmd += ['-t', str(timeout)]
      if memlimit is not None:
        timeoutcmd += ['-m', str(memlimit)]
        
      cmdline = timeoutcmd + cmdline
    
    p = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
    self.result, self.error = p.communicate(stdin)
    
    if p.returncode != 0:
      # Filter the output to see whether we exceeded time or memory:
      TIMEOUT_RE = 'TIMEOUT CPU (?P<cpu>\d+[.]\d*) MEM (?P<mem>\d+) MAXMEM (?P<maxmem>\d+) STALE (?P<stale>\d+)'
      m = re.search(TIMEOUT_RE, self.error, re.DOTALL)
      print m
      if m is not None:
        print m.groupdict()
        raise Timeout(self.result, self.error)
      
      MEMLIMIT_RE = 'MEM CPU (?P<cpu>\d+[.]\d*) MEM (?P<mem>\d+) MAXMEM (?P<maxmem>\d+) STALE (?P<stale>\d+)'
      m = re.search(MEMLIMIT_RE, self.error, re.DOTALL)
      print m
      if m is not None:
        print m.groupdict()
        raise OutOfMemory(self.result, self.error)
      
      raise ToolException(cmdline, p.returncode, self.result, self.error)
            
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
cliquegame = Tool('cliquegame', __LOG)
clusteredrandomgame = Tool('clusteredrandomgame', __LOG)
jurdzinskigame = Tool('jurdzinskigame', __LOG)
laddergame = Tool('laddergame', __LOG)
modelcheckerladder = Tool('modelcheckerladder', __LOG)
randomgame = Tool('randomgame', __LOG)
recursiveladder = Tool('recursiveladder', __LOG)
steadygame = Tool('steadygame', __LOG)

