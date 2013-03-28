import copy
import logging
import optparse
import os
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

_XYSIZE_QUERY = '''
SELECT (X.vertices + X.edges) as xval,
       (Y.vertices + Y.edges) as yval,
       cases.name 
FROM gamesizes X, gamesizes Y, games gx, games gy, instances, cases
WHERE X.id = gx.id 
  AND Y.id = gy.id
  AND gx.instance = gy.instance
  AND gx.reduction = "{0}"
  AND gy.reduction = "{1}"
  AND gy.instance = instances.id
  AND gx.instance = instances.id
  AND instances.caseid = cases.id
'''

_XSIZE_QUERY = '''
SELECT (X.vertices + X.edges) as xval,
       Y.{0} as yval,
       cases.name
FROM gamesizes X, gamesizes Y, games gx, games gy, instances, cases
WHERE X.id = gx.id 
  AND Y.id = gy.id
  AND gx.instance = gy.instance
  AND gx.reduction = "{1}"
  AND gy.reduction = "{2}"
  AND gy.instance = instances.id
  AND gx.instance = instances.id
  AND instances.caseid = cases.id
  AND yval IS NOT NULL
'''

_YSIZE_QUERY = '''
SELECT X.{0} as xval,
       (Y.vertices + Y.edges) as yval,
       cases.name
FROM gamesizes X, gamesizes Y, games gx, games gy, instances, cases
WHERE X.id = gx.id 
  AND Y.id = gy.id
  AND gx.instance = gy.instance
  AND gx.reduction = "{1}"
  AND gy.reduction = "{2}"
  AND gy.instance = instances.id
  AND gx.instance = instances.id
  AND instances.caseid = cases.id
  AND xval IS NOT NULL
'''

_QUERY = '''
SELECT X.{0} as xval,
       Y.{1} as yval,
       cases.name 
FROM gamesizes X, gamesizes Y, games gx, games gy, instances, cases
WHERE X.id = gx.id 
  AND Y.id = gy.id
  AND gx.instance = gy.instance
  AND gx.reduction = "{2}"
  AND gy.reduction = "{3}"
  AND gy.instance = instances.id
  AND gx.instance = instances.id
  AND instances.caseid = cases.id
  AND xval IS NOT NULL
  AND yval IS NOT NULL
'''

def query(conn, xcase, ycase, xval, yval):
  c = conn.cursor()
  if xval == 'size' and yval == 'size':
    return c.execute(_XYSIZE_QUERY.format(xcase, ycase))
  elif xval == 'size':
    return c.execute(_XSIZE_QUERY.format(yval, xcase, ycase))
  elif yval == 'size':
    return c.execute(_YSIZE_QUERY.format(xval, xcase, ycase))
  else:
    return c.execute(_QUERY.format(xval, yval, xcase, ycase))
  
# Compute the data that should be plotted.
# key determines the field that is used (sizes or times)
# aggregationFunction is a function that gives the result for one equivalence
# data is the data set
# equiv1 and equiv2 are the equivalences we are comparing.
def getplotdata(conn, xcase, ycase, xval, yval):
  LOG.debug("Getting plot data for ({0}, {1}) with X={2} and Y={3}".format(xcase, ycase, xval, yval))
  
  data = query(conn, xcase, ycase, xval, yval)
  
  for row in data:
    yield(row[0],row[1],getCluster(row[2]))
  
  
def scatterplot(plotcase, conn):
  values = '\n        '.join(
    ['{0}, {1}, {2}'.format(x, y, cluster) 
     for x, y, cluster in getplotdata(conn, plotcase['xcase'], plotcase['ycase'], plotcase['xval'], plotcase['yval'])])
  LOG.debug(values)
  latexsrc = open('templatesize.txt').read()
  for lbl in ('xmode', 'ymode', 'Xlabel', 'Ylabel'):
    latexsrc = latexsrc.replace('%' + lbl, str(plotcase[lbl]))
  return latexsrc.replace('%values', values)

def run(plotspec, dbfile):
  cases = yaml.load(open(plotspec).read())
  conn = sqlite3.connect(dbfile)
  
  for plot in cases:
    latexsrc = scatterplot(plot, conn)
    f = open("/tmp/{0}.tex".format(plot['jobname']), 'w')
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
