import logging
import optparse
import os
import yaml

def getcasetype(casename, casedata):
  LOG.debug('Getting type of case {0}'.format(casename))
  if casedata.has_key('properties'):
     return 'modelchecking'
  elif casedata.has_key('instances'):
    if casedata['instances'][0].has_key('compact'):
      return 'mlsolver'
    else:
      return 'equivalence'
  else:
    return 'pgsolver'

def loaddata(data, datadir, case=None):
  LOG.debug("Loading data with case {0}".format(case))
  if isinstance(data, list):
    for d in data:
      loaddata(d, datadir)
  else:
    assert isinstance(data, dict)
    if case is None and data.has_key('case'):
      case=data['case']
      type = getcasetype(case, data)
      
      if not data.has_key('properties') and not data.has_key('instances'):
        loaddata(data, datadir, case)
        
      for property in data.get('properties', []):
        loaddata(property, datadir, case)
      for instance in data.get('instances', []):
        loaddata(instance, datadir, case)
          
    else:
      # Instance level
      name = data.get('property', None)
      if name is None:
        name = data.get('compact', None)
      if name is None:        
        name = data.get('equivalence', None)
      if name is None:
        name = 'default'
      
      #LOG.info("Instance {0}".format(instanceid))
      LOG.info("Processing {0} -- {1}".format(case, name))
      LOG.debug("Data: {0}".format(data))
      
      yamlfile = data.get('files',{}).get('orig', None)
      LOG.debug("yamlfile: {0}".format(yamlfile))

      solution = data.get('solutions', {}).get('orig', {}).get('pbespgsolve', None)
      if solution == None:
        LOG.warning("No solution for {0} -- {1}".format(case, name))
      else:
        LOG.info("Solution: {0}".format(solution))

      f = open(yamlfile, 'r')
      details = yaml.load(f)
      f.close()
      details['Solution'] = solution
      f = open(yamlfile, 'w')
      f.write(yaml.dump(details, default_flow_style=False))
      f.close()



def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] resultfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 1:
    parser.error(parser.usage)
  
  resultfile = args[0]

  global LOG
  logging.basicConfig() 
  LOG = logging.getLogger()
  if options.verbosity > 0:
    LOG.setLevel(logging.INFO)
  if options.verbosity > 1:
    LOG.setLevel(logging.DEBUG)

  datadir = os.path.dirname(os.path.abspath(resultfile))
  data = yaml.load(open(resultfile, 'r'))
  loaddata(data, datadir)

if __name__ == '__main__':
  runCmdLine()
