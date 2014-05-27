##
# Insert parity game details into database.
# As input a list of yaml files is assumed, where
# each YAML file contains the detailed information of a single parity game.
# If the database already contains a parity game for the given case, the data
# is not added (i.e. we do not add duplicates)

import logging
import optparse
import os
import sqlite3
import yaml

def loaddetaildata(conn, gameid, detailfile, datadir):
  detailfile = os.path.join(datadir, detailfile[detailfile.find('cases/'):])
  try:
    data = yaml.load(open(detailfile, 'r'))
  except Exception as e:
    print e
    return
  
  c = conn.cursor()
  query = '''
  UPDATE gamesizes
  SET vertices=?,
      edges=?,
      even_vertices=?,
      odd_vertices=?,
      priorities=?,
      alternation_depth=?,
      alternation_depth_cks93=?,
      bfs_height=?,
      bfs_max_queue=?,
      bfs_back_level_edges=?,
      dfs_maxstack=?,
      diameter=?,
      diamonds=?,
      even_diamonds=?,
      odd_diamonds=?,
      girth=?,
      avg_degree=?,
      max_degree=?,
      min_degree=?,
      avg_indegree=?,
      max_indegree=?,
      min_indegree=?,
      avg_outdegree=?,
      max_outdegree=?,
      min_outdegree=?,
      avg_1_neighbourhood=?,
      max_1_neighbourhood=?,
      min_1_neighbourhood=?,
      avg_2_neighbourhood=?,
      max_2_neighbourhood=?,
      min_2_neighbourhood=?,
      avg_3_neighbourhood=?,
      max_3_neighbourhood=?,
      min_3_neighbourhood=?,
      sccs=?,
      scc_quotient_height=?,
      terminal_sccs=?,
      trivial_sccs=?
    WHERE id=?'''

  c.execute(query,
            (data.get('Graph',{}).get('Number of vertices', None),
            data.get('Graph',{}).get('Number of edges', None),
            data.get('Graph',{}).get('Number of even vertices', None),
            data.get('Graph',{}).get('Number of odd vertices', None),
            data.get('Graph',{}).get('Number of priorities', None),
            data.get('Alternation depth (priority ordering)', {}).get('value', None),
            data.get('Alternation depth [CKS93]', {}).get('value', None),
            data.get('BFS', {}).get('Number of levels (BFS height)', None),
            data.get('BFS', {}).get('Max queue', None),
            data.get('BFS', {}).get('Number of back level edges', None),
            data.get('DFS', {}).get('Max stack', None),
            data.get('Diameter', {}).get('value', None),
            data.get('Diamonds', {}).get('Total', None),
            data.get('Diamonds', {}).get('Even', None),
            data.get('Diamonds', {}).get('Odd', None),
            data.get('Girth', {}).get('value', None),
            data.get('Graph', {}).get('Degree', {}).get('avg', None),
            data.get('Graph', {}).get('Degree', {}).get('max', None),
            data.get('Graph', {}).get('Degree', {}).get('min', None),
            data.get('Graph', {}).get('In-degree', {}).get('avg', None),
            data.get('Graph', {}).get('In-degree', {}).get('max', None),
            data.get('Graph', {}).get('In-degree', {}).get('min', None),
            data.get('Graph', {}).get('Out-degree', {}).get('avg', None),
            data.get('Graph', {}).get('Out-degree', {}).get('max', None),
            data.get('Graph', {}).get('Out-degree', {}).get('min', None),
            data.get('Neighbourhood', {}).get(1, {}).get('avg', None),
            data.get('Neighbourhood', {}).get(1, {}).get('max', None),
            data.get('Neighbourhood', {}).get(1, {}).get('min', None),
            data.get('Neighbourhood', {}).get(2, {}).get('avg', None),
            data.get('Neighbourhood', {}).get(2, {}).get('max', None),
            data.get('Neighbourhood', {}).get(2, {}).get('min', None),
            data.get('Neighbourhood', {}).get(3, {}).get('avg', None),
            data.get('Neighbourhood', {}).get(3, {}).get('max', None),
            data.get('Neighbourhood', {}).get(3, {}).get('min', None),
            data.get('SCC', {}).get('SCCs', None),
            data.get('SCC', {}).get('Quotient height', None),
            data.get('SCC', {}).get('Terminal SCCs', None),
            data.get('SCC', {}).get('Trivial SCCs', None),
            gameid)) 
  
def split_modelchecking(case):
  name = None
  pos = case.find('infinitely_often')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('invariantly_')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('read_then_eventually')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('no_generation')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('no_duplication')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('nodeadlock')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('eventually')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('property')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('safety')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('liveness')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('3.2._max_copies_per_region')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]
  pos = case.find('counting')
  if pos != -1:
    name = case[pos:]
    case = case[:pos-1]

  pos = case.find('nparties')
  if pos != -1:
    case = case[:pos].replace('_', ' ') + ' [' + case[pos:] + ']'
    case = case.replace('_', ', ')
    return (name, case)
  pos = case.find('datasize')
  if pos != -1:
    case = case[:pos] + ' [' + case[pos:] + ']'
    case = case.replace('_', ', ')
    return (name, case)
  pos = case.find('nlifts')
  if pos != -1:
    case = case[:pos].replace('_', ' ') + ' [' + case[pos:] + ']'
    case = case.replace('_', ', ')
    return (name, case)
  pos = case.find('ndisks')
  if pos != -1:
    case = case[:pos].replace('_', ' ') + ' [' + case[pos:] + ']'
    case = case.replace('_', ', ')
    return (name, case)
  
  return (name, case)

def split_equivalence(case):
  name = None
  pos = case.find('eq=')
  if pos != -1:
    name = case[pos+3:]
    case = case[:pos]

  pos = case.rfind('(')
  if pos != -1:
    case = case[:pos-1].replace(')_', ')/').replace('_(',' (').replace('_', '/') + ' ' + case[pos:].replace('_', ', ')

  return (name, case)

def gettool(type):
  if type == 'equivchecking' or type == 'modelchecking':
    return 'pbes2bes'
  else:
    return type

def loaddata(conn, data, datadir, store_reduced, caseid=None):
  if isinstance(data, list):
    for d in data:
      loaddata(conn, d, datadir, store_reduced)
  else:
    data = data.strip()
    case = None
    name = 'default'
    if data.find('modelchecking') != -1:
      type = 'modelchecking'
      case = data[data.rfind('/')+1:-5]
      (name, case) = split_modelchecking(case)
    elif data.find('equivchecking') != -1:
      type = 'equivalence'
      case = data[data.rfind('/')+1:-5]
      (name, case) = split_equivalence(case)
    elif data.find('mlsolver') != -1:
      type = 'mlsolver'
      case = data[data.rfind('/')+1:-5].replace('_', ' ')
      if case.find('compact') != -1:
        name = 'True'
        case = case.replace(' compact', '')
      else:
        name = 'False'
      pos = case.find('n=')
      if pos != -1:
        case = case[:pos] + ' [' + case[pos:] + ']'
      else:
        LOG.warning('MLSolver case without n value')
    elif data.find('pgsolver') != -1:
      type = 'pgsolver'
      case = data[data.rfind('/')+1:-5].replace('_', ' ')
    else:
      raise Exception('Could not determine type of {0}'.format(data))

    LOG.debug('Processing case {0}:\n  type = {1}\n  case = {2}\n  name = {3}'.format(data, type, case, name))

    # Insert case if it is not yet in the data base
    c = conn.cursor()
    c.execute('SELECT * FROM cases WHERE name=? AND type=?', (case, type))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO cases VALUES (null, ?, ?)', (case, type))
      caseid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      LOG.debug("Inserted new case {0} with id {1}".format(case, caseid))
    else:
      caseid = result[0]
      LOG.debug("Retrieved existing case {0} with id {1}".format(case, caseid))

    # Insert instance if not yet in the data base

    c.execute('SELECT * FROM instances WHERE caseid = ? AND name = ?', (caseid, name))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO instances VALUES (null, ?, ?)', (caseid, name))
      instanceid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      LOG.info("Inserted new instance {0} with id {1}".format(name, instanceid))
    else:
      instanceid = result[0]
      LOG.info("Retrieved existing instance {0} with id {1}".format(name, instanceid))
    
    
    yamlfile = data
    gmfile = os.path.splitext(yamlfile)[0].replace('/data/','/temp/') + '.gm'
    reduction = 'orig'

    # Insert parity game
    c.execute('SELECT * FROM games WHERE instance = ? AND reduction = ? and file = ?', (instanceid, reduction, gmfile))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO games VALUES (null, ?, ?, ?)', (instanceid, reduction, gmfile))
      gameid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      LOG.info("Inserted new game {0} with id {1}".format(gmfile, gameid))
    else:
      gameid = result[0]      
      LOG.info("Retrieved existing game {0} with id {1}".format(gmfile, gameid))

    # Insert generation info
    print gameid
    c.execute('SELECT * FROM generation WHERE id = ?', (gameid,))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO generation VALUES (?, ?, ?)', (gameid, None, gettool(type)))

    # Get reduction
    c.execute('SELECT * FROM reduction WHERE idfrom = ? AND idto = ?', (gameid, gameid))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO reduction VALUES (null, ?, ?, ?, ?)', (gameid, gameid, 'dummy', 0.0))

    # Solving info
    c.execute('SELECT * FROM solving where id = ?', (gameid,))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO solving VALUES (?, ?, ?, ?)', (gameid, None, None, None))

    # Create entry for sizes
    c.execute('SELECT * FROM gamesizes WHERE id = ?', (gameid,))
    result = c.fetchone()
    if result is None:
      c.execute('INSERT INTO gamesizes (id) VALUES (?)', (gameid,))

    conn.commit()

    loaddetaildata(conn, gameid, yamlfile, datadir)
    conn.commit()
        
def run(resultfile, sqlitefile, initialise, store_reduced):
  LOG.info("Loading files from {0}".format(resultfile))
  LOG.info("Storing games to {0}".format(sqlitefile))
  conn = sqlite3.connect(sqlitefile)
  datadir = os.path.dirname(os.path.abspath(resultfile))
  
  r = open(resultfile, 'r')
  data = r.readlines()
  
  loaddata(conn, data, datadir, store_reduced)
  
  conn.commit()  
  conn.close()

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] resultfile sqlitefile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  resultfile = args[0]
  sqlitefile = args[1]

  global LOG
  logging.basicConfig() 
  LOG = logging.getLogger()
  if options.verbosity > 0:
    LOG.setLevel(logging.INFO)
  if options.verbosity > 1:
    LOG.setLevel(logging.DEBUG)
  
  run(resultfile, sqlitefile, False, False)

if __name__ == '__main__':
  runCmdLine()
