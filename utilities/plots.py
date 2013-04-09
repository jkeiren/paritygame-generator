import logging
import optparse
import os
import string
import subprocess
import sqlite3
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

_QUERY = '''
SELECT X.{0} as xval,
       Y.{1} as yval,
       cases.name 
FROM query_gamesizes X, query_gamesizes Y, games gx, games gy, instances, cases
WHERE X.id = gx.id 
  AND Y.id = gy.id
  AND gx.instance = gy.instance
  AND gx.reduction = "{2}"
  AND gy.reduction = "{3}"
  AND gy.instance = instances.id
  AND gx.instance = instances.id
  AND instances.caseid = cases.id
  {4}
  {5}
'''

def query(conn, xcase, ycase, xval, yval):
  c = conn.cursor()
  xvalnull = '' if xval == 'times' else 'AND xval IS NOT NULL'
  yvalnull = '' if yval == 'times' else 'AND yval IS NOT NULL '
  LOG.debug("Executing query {0}".format(_QUERY.format(xval, yval, xcase, ycase, xvalnull, yvalnull)))
  return c.execute(_QUERY.format(xval, yval, xcase, ycase, xvalnull, yvalnull))
  
# Compute the data that should be plotted.
# key determines the field that is used (sizes or times)
# aggregationFunction is a function that gives the result for one equivalence
# data is the data set
# equiv1 and equiv2 are the equivalences we are comparing.
def getplotdata(conn, xcase, ycase, xval, yval, xmode = None, ymode = None):
  LOG.debug("Getting plot data for ({0}, {1}) with X={2} and Y={3}".format(xcase, ycase, xval, yval))
  
  data = query(conn, xcase, ycase, xval, yval)
  
  for row in data:
    LOG.debug("  got {0} in cluster {1}".format(row, getCluster(row[2])))
    x,y = row[0], row[1]
    if xval == 'times':
      if x is None:
        x = 3600.0
      x = max(min([x, 3600.0]),0.1)
    if yval == 'times':
      if y is None:
        y = 3600.0
      y = max(min([y, 3600.0]),0.1)
    
    #if xval != 'times' and xmode == 'log' and float(x) == float(0):
    #  x = 1
    #if yval != 'times' and ymode == 'log' and float(y) == float(0):
      #y = 1
    yield (x,y,getCluster(row[2]))
  
  
def scatterplot(plotcase, conn):
  values = '\n        '.join(
    ['{0}, {1}, {2}'.format(x, y, cluster) 
     for x, y, cluster in getplotdata(conn, plotcase['xcase'], plotcase['ycase'], plotcase['xval'], plotcase['yval'], plotcase['xmode'], plotcase['ymode'])])
  LOG.debug(values)
  latexsrc = open('templatescatter.txt').read()
  for lbl in ('xmode', 'ymode', 'Xlabel', 'Ylabel'):
    latexsrc = latexsrc.replace('%' + lbl, str(plotcase[lbl]))
  maxes = ''
  if plotcase.has_key('xmax'):
    maxes = maxes + ",xmax={0}".format(plotcase['xmax'])
  if plotcase.has_key('ymax'):
    maxes += ",ymax={0}".format(plotcase['ymax'])
  latexsrc = latexsrc.replace('%maxes', maxes)
  return latexsrc.replace('%values', values)

def histogram(plotcase, conn):
  values = '\n        '.join(
    [r'{0:.2f}'.format(100.0 - 100.0 * float(y) / float(x))
     for x, y, cluster in getplotdata(conn, plotcase['xcase'], plotcase['ycase'], plotcase['xval'], plotcase['yval'])])
  latexsrc = open('templatehist.txt').read()
  return latexsrc.replace('%values', values)

def boxplot(plotcase, conn):
  LOG.debug("Creating boxplot for case {0}".format(plotcase))
  values = [(x, y, cluster) for x, y, cluster in getplotdata(conn, plotcase['xcase'], plotcase['ycase'], plotcase['xval'], plotcase['yval'])]
  LOG.debug("Obtained {0} values".format(len(values)))
  data = []
  for cluster in clusters.keys():
    clustervalues = filter(lambda x: x[2] == cluster, values)
    if clustervalues == []: continue
    reductions = map(lambda x: 100.0 - 100.0 * float(x[1]) / float(x[0]), clustervalues)
    min_ = min(reductions + [100])
    avg = sum(reductions) / len(reductions)
    max_ = max(reductions + [0])
    data.append((cluster, min_, avg, max_))
  
  print data  
  coords = ['{:20}, {:5}, {:6.2f}, {:6.2f}, {:6.2f}'.format(case, n, avg, min_, max_ - min_) for n, (case, min_, avg, max_) in enumerate(data)]
  latexsrc = string.Template(open('templatebox.txt').read())
  if plotcase.get('yticklabels', True):
    cases = ','.join([x[0] for x in data])
  else:
    cases = ""
  return latexsrc.substitute(cases = cases, table = '\n    '.join(coords))

def run(plotspec, dbfile):
  cases = yaml.load(open(plotspec).read())
  conn = sqlite3.connect(dbfile)
  
  for plot in cases:
    if not plot.has_key('format'):
      LOG.warning("No plot format specified")
      continue
    
    if plot['format'] == 'scatterplot':
      latexsrc = scatterplot(plot, conn)
    elif plot['format'] == 'boxplot':
      latexsrc = boxplot(plot, conn)
    elif plot['format'] == 'histogram':
      latexsrc = histogram(plot, conn)
    else:
      LOG.warning("Unknown plot format {0}".format(plot['format']))
      continue
    f = open('/tmp/{0}.tex'.format(plot['jobname']), 'w')
    f.write(latexsrc)
    f.close()
    pdflatex = subprocess.Popen(['pdflatex', '-jobname=' + plot['jobname']], stdin=subprocess.PIPE)
    pdflatex.communicate(latexsrc)
    os.unlink('{0}.aux'.format(plot['jobname']))
    os.unlink('{0}.log'.format(plot['jobname']))

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] plotspec dbfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  plotspec = args[0]
  dbfile = args[1]

  global LOG
  logging.basicConfig() 
  LOG = logging.getLogger('plot')
  if options.verbosity > 0:
    LOG.setLevel(logging.INFO)
  if options.verbosity > 1:
    LOG.setLevel(logging.DEBUG)
  
  run(plotspec, dbfile)

if __name__ == '__main__':
  runCmdLine()
