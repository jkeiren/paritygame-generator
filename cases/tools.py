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
  def __init__(self, tool, exitcode, result):
    Exception.__init__(self)
    self.__result = result
    self.__ret = exitcode
    self.__cmdline = ' '.join(tool)
  
  def __str__(self):
    return 'The commandline "{0}" failed with exit code "{1}".\nStandard error:\n{2}\nStandard output:\n{3}\n'.format(
      self.__cmdline, self.__ret, self.__result['err'], self.__result['out'])

class Timeout(Exception):
  def __init__(self, cmdline, result):
    super(Timeout, self).__init__()
    self.__cmdline = ' '.join(cmdline)
    self.result = result
    
  def __str__(self):
    return 'The commandline "{0}" timed out'.format(self.__cmdline)
    
class OutOfMemory(Exception):
  def __init__(self, cmdline, result):
    super(OutOfMemory, self).__init__()
    self.__cmdline = ' '.join(cmdline)
    self.result = result
    
  def __str__(self):
    return 'The commandline "{0}" exceeded the memory limit'.format(self.__cmdline)

class Tool(object):
  def __init__(self, name, log, hastimings = True, filter_=None, timed=False, timeout=None, memlimit=None):
    self.__name = name
    self.__log = log
    self.__hastimings = hastimings
    self.__timeout = timeout
    self.__memlimit = memlimit 
    self.__filter = filter_
    self.__timed = timed
    self.result = {}
    self.result['cmdline'] = None
    self.result['out'] = None
    self.result['err'] = None
    self.result['filter'] = None
    self.result['times'] = None    
    self.result['memory'] = 'unknown'
    
  def __run(self, stdin, stdout, stderr, timeout, memlimit, *args, **kwargs):
    cmdline = kwargs.pop('prependcmdline', [])
    if kwargs:
      raise TypeError('Unknown parameter(s) for run instance: ' + 
                      ', '.join(['{0}={1}'.format(k, v) 
                                 for k, v in kwargs.items()]))
    cmdline += [self.__name] + [str(x) for x in args]
    self.__log.info('Running {0}'.format(' '.join(cmdline)))
    self.result['cmdline'] = ' '.join(cmdline)
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
    out, err = p.communicate(stdin)
    self.result['out'], self.result['err'] = out, err 
    
    if p.returncode != 0:
      # Filter the output to see whether we exceeded time or memory:
      TIMEOUT_RE = 'TIMEOUT CPU (?P<cpu>\d+[.]\d*) MEM (?P<mem>\d+) MAXMEM (?P<maxmem>\d+) STALE (?P<stale>\d+)'
      m = re.search(TIMEOUT_RE, self.result['err'], re.DOTALL)
      if m is not None:
        self.result['times'] = 'timeout'
        raise Timeout(cmdline, self.result)
      
      MEMLIMIT_RE = 'MEM CPU (?P<cpu>\d+[.]\d*) MEM (?P<mem>\d+) MAXMEM (?P<maxmem>\d+) STALE (?P<stale>\d+)'
      m = re.search(MEMLIMIT_RE, self.result['err'], re.DOTALL)
      if m is not None:
        self.result['memory'] = 'outofmemory'
        raise OutOfMemory(cmdline, self.result)
      
      raise ToolException(cmdline, p.returncode, self.result)
            
  def __run_timed(self, stdin, stdout, stderr, timeout, memlimit, *args):
    if self.__hastimings:
      timings = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
      timings.close()
      self.__run(stdin, stdout, stderr, timeout, memlimit, '--timings='+timings.name, *args)
      t = yaml.load(open(timings.name).read())
      os.unlink(timings.name)
      self.result['times'] = t[0]['timing']
    else:
      timings = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
      timings.close()
      cmdline=['/usr/bin/time', '--format', '{user: %U, sys: %S}', '-o', timings.name]
      self.__run(stdin, stdout, stderr, timeout, memlimit, *args, prependcmdline=cmdline)
      t = yaml.load(open(timings.name).read())
      os.unlink(timings.name)
      self.result['times'] = {}
      self.result['times']['total'] = t['sys'] + t['user']
  
  def __apply_filter(self, filter_):
    m = re.search(filter_, self.error, re.DOTALL)
    if m is not None:
      self.result['filter'] = m.groupdict()
    else:
      self.__log.error('No match!')
      self.__log.error(filter_)
      self.__log.error(self.result['err'])
      self.result['filter'] = {}
  
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
    self.__log.debug(self.result['err'])
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
pgsolver = Tool('pgsolver', __LOG, hastimings = False)
mlsolver = Tool('mlsolver', __LOG, hastimings = False)
PGCONVERT_RE = 'Parity game contains (?P<vorig>\d+) nodes and (?P<eorig>\d+) edges\..*?Parity game contains (?P<vred>\d+) nodes and (?P<ered>\d+) edges after[^[]*$'
pgconvert = Tool('pgconvert', __LOG, filter_=PGCONVERT_RE)
transformer = Tool('transformer', __LOG, hastimings = False)
LTSMIN_RE = 'original LTS has (?P<V>\d+) .*? (?P<E>\d+) .*?' \
  '(?:marking divergences took .*? (?P<ptimeu>\d+.\d+) user (?P<ptimes>\d+.\d+) sys.*?)?' \
  'reduction took .*? (?P<rtimeu>\d+.\d+) user (?P<rtimes>\d+.\d+) sys.*?' \
  'reduced LTS has (?P<Vr>\d+) .*? (?P<Er>\d+)'
ltsmin = Tool('ltsmin', __LOG, filter_=LTSMIN_RE, hastimings = False)
lpsbisim2pbes = Tool('lpsbisim2pbes', __LOG)
towersofhanoi = Tool('towersofhanoi', __LOG, hastimings = False)
towersofhanoi_alt = Tool('towersofhanoi_alt', __LOG, hastimings = False)
elevatorverification = Tool('elevatorverification', __LOG, hastimings = False)
elevatorverification_alt = Tool('elevatorverification_alt', __LOG, hastimings = False)
cliquegame = Tool('cliquegame', __LOG, hastimings = False)
clusteredrandomgame = Tool('clusteredrandomgame', __LOG, hastimings = False)
jurdzinskigame = Tool('jurdzinskigame', __LOG, hastimings = False)
laddergame = Tool('laddergame', __LOG, hastimings = False)
modelcheckerladder = Tool('modelcheckerladder', __LOG, hastimings = False)
randomgame = Tool('randomgame', __LOG, hastimings = False)
recursiveladder = Tool('recursiveladder', __LOG, hastimings = False)
steadygame = Tool('steadygame', __LOG, hastimings = False)

