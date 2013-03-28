import copy
import logging
import optparse
import os
import subprocess
import yaml

LOG = None

clusters = {
  'modelchecking': ['Debug spec', 'Lift (Correct)', 'Lift (Incorrect)', 'ABP', \
                     'ABP(BW)', 'CABP', 'Par', 'SWP', 'Leader', 'Othello', \
                     'Clobber', 'Snake', 'Hex', 'Domineering', 'Hanoi', \
                     'Elevator', 'CCP', 'Hesselink', 'Onebit', 'BRP', \
                     'elevatorverification', 'towersofhanoi'],
  'equivalence':   ['Buffer/', 'ABP/', 'ABP(BW)/','CABP/','Par/','Onebit/','SWP/','Hesselink/'],
  'specialcases':  ['cliquegame', 'jurdzinskigame', 'laddergame', \
                    'modelcheckerladder', 'recursiveladder'],
  'random': ['randomgame', 'clusteredrandomgame', 'steadygame'],
  'mlsolver': ['Include', 'Nester', 'StarNester', 'Petri', 'ParityAndBuechi', \
               'MuCalcLimitClosure', 'FLCTLLimitClosure', \
               'FLCTLStarLimitClosure', 'FLCTLStarSimpleLimitClosure', \
               'DemriKillerFormula', 'FairScheduler', 'LTMucalcBinaryCounter', \
               'CTLStarBinaryCounter', 'PDLBinaryCounter', 'HugeModels'],
}

# Determine to which cluster this case belongs
def getCluster(case):
  for (cluster,names) in clusters.iteritems():
    for name in names:
      if case.startswith(name) and not case.startswith('{0}/'.format(name)):
        return cluster
  assert False

# Number of vertices + number of edges
def sizesum(sizes, equiv):
  return int(sizes[equiv]['vertices']) + int(sizes[equiv]['edges'])

def gentime(generation):
  print generation
  if generation.get('times', {}).has_key('total'):
    return generation['times']['total']
  else:
    return 3600.0

# Determine the time required for reduction + solving for equiv.
def mintime(times, equiv):
  if equiv == 'orig':
    equiv = 'original'
  reductiontime = times[equiv].pop('reduction',{}).pop('reduction', 0.0)
  
  offset = float(reductiontime)
  filteredtimes = []
  if times[equiv]['pbespgsolve'] not in ['timeout', 'unknown']:
    filteredtimes.append(times[equiv]['pbespgsolve']['solving'])
  result = max(0.01, min(offset + min(filteredtimes + [3600.0]), 3600.0))
  return result

def detailFile(data, case):
  f = data['files'][case]
  f = f[f.find('cases'):]
  return os.path.join(RESULT_DIR,f)

def detailData(data, case):
  return yaml.load(open(detailFile(data, case), 'r'))

def getsize(data, case):
  if case == 'original':
    case = 'orig'
  return data['sizes'][case]['vertices'] + data['sizes'][case]['edges']

def getalternationDepth(data, case):
  return detailData(data,case)['Alternation depth (priority ordering)']['value']

def getAvgDegree(data, case):
  return detailData(data,case)['Graph']['Degree']['avg']

def getMaxOutDegree(data, case):
  return detailData(data,case)['Graph']['Out-degree']['max']

def getMaxInDegree(data, case):
  return detailData(data,case)['Graph']['In-degree']['max']

def getNumSCCs(data, case):
  return detailData(data,case)['SCC']['SCCs']

def getNontrivialSCCs(data, case):
  SCCs = detailData(data,case)['SCC']
  return SCCs['SCCs'] - SCCs['Trivial SCCs']

def getDiamonds(data, case):
  return detailData(data,case)['Diamonds']['Total']

def getDiameter(data, case):
  return detailData(data,case)['Diameter']['value']

getter = {
  'size': getsize,
  'alternation_depth': getalternationDepth,
  'avg_degree': getAvgDegree,
  'max_indegree': getMaxInDegree,
  'max_outdegree': getMaxOutDegree,
  'sccs': getNumSCCs,
  'nontrivial_sccs': getNontrivialSCCs,
  'diamonds': getDiamonds,
  'diameter': getDiameter
}

# Compute the data that should be plotted.
# key determines the field that is used (sizes or times)
# aggregationFunction is a function that gives the result for one equivalence
# data is the data set
# equiv1 and equiv2 are the equivalences we are comparing.
def getplotdata(data, xcase, ycase, xval, yval):
  LOG.debug("Getting plot data for ({0}, {1}) with X={2} and Y={3}".format(xcase, ycase, xval, yval))
  if isinstance(data, list): # top level
    for d in data:
      for p in getplotdata(d, xcase, ycase, xval, yval):
        yield p
  else: # deeper nesting.
#    print data
    assert isinstance(data, dict)
    if data.has_key('case') and (data.has_key('properties') or data.has_key('instances')):
      # High level case, we have some varieties
      if data.has_key('properties'): # Model checking
        instances = data.get('properties')
      else:
        assert data.has_key('instances') # Equivalence checking or MLSolver
        instances = data.get('instances')

      for instance in instances:
        for point in getplotdata(instance, xcase, ycase, xval, yval):
          yield (point[0], point[1], getCluster(data['case']))
      
    else: # We are in pretty deep!
      if data.has_key('case'):
        try:
          yield (getter[xval](data, xcase), getter[yval](data, ycase), getCluster(data['case']))
        except:
          pass
      else:
        try:
          yield (getter[xval](data, xcase), getter[yval](data, ycase))
        except:
          pass


def scatterplot(plotcase, results):
  LOG.debug("Results: {0}".format(results))
  LOG.debug("case: {0}".format(plotcase))
  values = '\n        '.join(
    ['{0}, {1}, {2}'.format(x, y, cluster) 
     for x, y, cluster in getplotdata(results, plotcase['xcase'], plotcase['ycase'], plotcase['xval'], plotcase['yval'])])
  LOG.debug(values)
  latexsrc = open('templatesize.txt').read()
  for lbl in ('xmode', 'ymode', 'Xlabel', 'Ylabel'):
    latexsrc = latexsrc.replace('%' + lbl, str(plotcase[lbl]))
  return latexsrc.replace('%values', values)

def run(plotspec, resultfile):
  cases = yaml.load(open(plotspec).read())
  results = yaml.load(open(resultfile).read())

  for plot in cases:
    latexsrc = scatterplot(plot, copy.deepcopy(results))
    f = open("/tmp/{0}.tex".format(plot['jobname']), 'w')
    f.write(latexsrc)
    f.close()
    pdflatex = subprocess.Popen(['pdflatex', '-jobname=' + plot['jobname']], stdin=subprocess.PIPE)
    pdflatex.communicate(latexsrc)

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] plotspec resultfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  plotspec = args[0]
  resultfile = args[1]

  global LOG
  logging.basicConfig() 
  LOG = logging.getLogger('plot')
  if options.verbosity > 0:
    LOG.setLevel(logging.INFO)
  if options.verbosity > 1:
    LOG.setLevel(logging.DEBUG)
  
  global RESULT_DIR
  RESULT_DIR=os.path.dirname(os.path.abspath(resultfile))
  run(plotspec, resultfile)

if __name__ == '__main__':
  runCmdLine()
