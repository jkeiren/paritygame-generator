import copy
import logging
import optparse
import string
import subprocess
import yaml

LOG = None

clusters = {
  'modelchecking': ['Debug spec', 'Lift (Correct)', 'Lift (Incorrect)', 'ABP', 'ABP(BW)', 'CABP', 'Par', 'SWP', 'Leader', 'Othello', 'Clobber', 'Snake', 'Hex', 'Domineering', 'Hanoi', 'Elevator', 'CCP', 'Hesselink', 'Onebit', 'BRP', 'elevatorverification', 'towersofhanoi'],
  'equivalence':   ['Buffer/', 'ABP/', 'ABP(BW)/','CABP/','Par/','Onebit/','SWP/','Hesselink/'],
  'specialcases':  [],
  'mlsolver': []
}

def getCluster(case):
  for (cluster,names) in clusters.iteritems():
    for name in names:
      if case.startswith(name) and not case.startswith('{0}/'.format(name)):
        return cluster
  assert False

def sizesum(sizes, equiv):
  return int(sizes[equiv]['vertices']) + int(sizes[equiv]['edges'])

def mintime(times, equiv):
  if equiv == 'orig':
    equiv = 'original'
  reductiontime = times[equiv].pop('reduction',{}).pop('reduction', 0.0)
  
  offset = float(reductiontime)
  filteredtimes = []
  if times[equiv]['pbespgsolve'] not in ['timeout', 'unknown']:
    filteredtimes.append(times[equiv]['pbespgsolve']['solving'])
  result = max(0.01, min(offset + min(filteredtimes + [1800.0]), 1800.0))
  return result

def getplotdata(key, aggregationFunction, data, equiv1, equiv2):
  LOG.debug("Getting plot data with key {0}, and equivalences {1} and {2}".format(key, equiv1, equiv2))
  if isinstance(data, list): # top level
    LOG.debug("A")
    for d in data:
      for p in getplotdata(key, aggregationFunction, d, equiv1, equiv2):
        yield p
  else: # deeper nesting.
    assert isinstance(data, dict)
    if data.has_key('case') and (data.has_key('properties') or data.has_key('instances')):
      LOG.debug("B")
      # High level case, we have some varieties
      if data.has_key('properties'): # Model checking
        instances = data.get('properties')
      else:
        assert data.has_key('instances') # Equivalence checking or MLSolver
        instances = data.get('instances')

      for instance in instances:
        for point in getplotdata(key, aggregationFunction, instance, equiv1, equiv2):
          yield (point[0], point[1], getCluster(data['case']))
      
    else: # We are in pretty deep!
      if data.has_key('case'):
        yield (aggregationFunction(data[key],equiv1), aggregationFunction(data[key],equiv2), getCluster(data['case']))
      else:
        yield (aggregationFunction(data[key],equiv1), aggregationFunction(data[key],equiv2))
 
# Define how to compute the plot points     
generators = {
  'sizes': lambda *args: getplotdata('sizes', sizesum, *args),
  'times': lambda *args: getplotdata('times', mintime, *args)  
}

def scatterplot(case, results):
  LOG.debug("Results: {0}".format(results))
  LOG.debug("case: {0}".format(case))
  values = '\n        '.join(
    ['{0}, {1}, {2}'.format(x, y, cluster) 
     for x, y, cluster in generators[case['type']](results, case['xval'], case['yval'])])
  LOG.debug(values)
  latexsrc = open('template.txt').read()
  for lbl in ('Xlabel', 'Ylabel', 'Xmin', 'Xmax', 'Ymin', 'Ymax'):
    latexsrc = latexsrc.replace('%' + lbl, str(case[lbl]))
  return latexsrc.replace('%values', values)
  pass

def histogram(case, results):
  values = '\n        '.join(
    [r'{0:.2f}'.format(100.0 - 100.0 * float(y) / float(x))
     for x, y, cluster in generators[case['type']](results, case['xval'], case['yval'])])
  for x, y, cluster in generators[case['type']](results, case['xval'], case['yval']):
    if y > x:
      print '!!!', y, x
  latexsrc = open('templatehist.txt').read()
  return latexsrc.replace('%values', values)

def boxplot(case, results):
  values = [(x, y, cluster) for x, y, cluster in generators[case['type']](results, case['xval'], case['yval'])]
  data = []
  for cluster in clusters.keys():
    clustervalues = filter(lambda x: x[2] == cluster, values)
    if clustervalues == []: continue
    reductions = map(lambda x: 100.0 - 100.0 * float(x[1]) / float(x[0]), clustervalues)
    min_ = min(reductions + [100])
    avg = sum(reductions) / len(reductions)
    max_ = max(reductions + [0])
    data.append((cluster, min_, avg, max_))
    
  coords = ['{:20}, {:5}, {:6.2f}, {:6.2f}, {:6.2f}'.format(case, n, avg, min_, max_ - min_) for n, (case, min_, avg, max_) in enumerate(data)]
  latexsrc = string.Template(open('templatepercase.txt').read())
  return latexsrc.substitute(cases = ','.join([x[0] for x in data]), table = '\n    '.join(coords))
  
def run(plotspec, resultfile):
  cases = yaml.load(open(plotspec).read())
  results = yaml.load(open(resultfile).read())

  for plot in cases:
    if plot.setdefault('format', 'scatter') == 'scatter':
      latexsrc = scatterplot(plot, copy.deepcopy(results))
    elif plot['format'] in ['histogram', 'hist']:
      latexsrc = histogram(plot, copy.deepcopy(results))
    else: # plot['format'] == 'boxplot'
      latexsrc = boxplot(plot, copy.deepcopy(results))
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
  
  run(plotspec, resultfile)

if __name__ == '__main__':
  runCmdLine()
