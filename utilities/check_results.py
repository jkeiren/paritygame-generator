import logging
import optparse
import yaml

def compareSolution(case, property, solution, case1, case2):
  if solution.has_key(case1) and solution[case1]['pbespgsolve'] != 'unknown' \
    and solution.has_key(case2) and solution[case1]['pbespgsolve'] != 'unknown' \
    and solution[case1]['pbespgsolve'].strip().split()[0] != solution[case2]['pbespgsolve'].strip().split()[0]:
    print 'The solutions differ for problem instance {0} -- {1}'.format(case, property)
    print '  solution of {0}: {1}'.format(case1, solution[case1]['pbespgsolve'])
    print '  solution of {0}: {1}'.format(case2, solution[case2]['pbespgsolve'])

def checkEqualSolutions(case, property, data):
  solution = data['solutions']
  compareSolution(case, property, solution, 'original', 'bisim')
  compareSolution(case, property, solution, 'original', 'fmib')
  compareSolution(case, property, solution, 'original', 'stut')
  compareSolution(case, property, solution, 'original', 'gstut')
  compareSolution(case, property, solution, 'bisim', 'stut')
  compareSolution(case, property, solution, 'bisim', 'fmib')
  compareSolution(case, property, solution, 'bisim', 'gstut')
  compareSolution(case, property, solution, 'fmib', 'gstut')
  compareSolution(case, property, solution, 'stut', 'gstut')

def compareSize(case, instance, size, case1, case2):
  if size.has_key(case1) and size.has_key(case2) and \
    int(size[case1]['vertices']) < int(size[case2]['vertices']):
    print 'The sizes differ for problem instance {0} -- {1}'.format(case, instance)
    print '  size of {0} = {1}'.format(case1, size[case1])
    print '  size of {0} = {1}'.format(case2, size[case2])

def checkSizes(case, property, data):
  size = data['sizes']
  compareSize(case, property, size, 'orig', 'bisim')
  compareSize(case, property, size, 'orig', 'fmib')
  compareSize(case, property, size, 'orig', 'stut')
  compareSize(case, property, size, 'orig', 'gstut')
  compareSize(case, property, size, 'bisim', 'stut')
  compareSize(case, property, size, 'bisim', 'fmib')
  compareSize(case, property, size, 'bisim', 'gstut')
  compareSize(case, property, size, 'fmib', 'gstut')
  compareSize(case, property, size, 'stut', 'gstut')
    

def run(infilename, outfilename, log):
  data = yaml.load(open(infilename).read())
  for case in data:
    if case.has_key('properties'):
      for property in case['properties']:
        checkEqualSolutions(case['case'], property['property'], property)
        checkSizes(case['case'], property['property'], property)
    if case.has_key('instances'):
      for equiv in case['instances']:
        checkEqualSolutions(case['case'], equiv['equivalence'], equiv)
        checkSizes(case['case'], equiv['equivalence'], equiv)

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 1:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = None  
  if len(args) >= 2:
    outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('pruning').setLevel(logging.INFO)
  
  run(infilename, outfilename, logging.getLogger('pruning'))

if __name__ == '__main__':
  runCmdLine()
