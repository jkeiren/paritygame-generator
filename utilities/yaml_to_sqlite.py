import logging
import optparse
import os
import sqlite3
import yaml

SCHEMA_QUERY = '''
  CREATE TABLE "cases" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL
);
CREATE TABLE "instances" (
    "id" INTEGER PRIMARY KEY,
    "caseid" INTEGER NOT NULL,
    "name" TEXT NOT NULL
);
CREATE TABLE "games" (
    "id" INTEGER PRIMARY KEY,
    "instance" INTEGER NOT NULL,
    "reduction" TEXT NOT NULL,
    "file" TEXT
);
CREATE TABLE "gamesizes" (
    "id" INTEGER PRIMARY KEY,
    "vertices" INTEGER DEFAULT NULL,
    "edges" INTEGER DEFAULT NULL,
    "priorities" INTEGER DEFAULT NULL,
    "even_vertices" INTEGER DEFAULT NULL,
    "odd_vertices" INTEGER DEFAULT NULL,
    "alternation_depth" INTEGER DEFAULT NULL,
    "alternation_depth_cks93" INTEGER DEFAULT NULL,
    "bfs_height" INTEGER DEFAULT NULL,
    "bfs_max_queue" INTEGER DEFAULT NULL,
    "bfs_back_level_edges" INTEGER DEFAULT NULL,
    "dfs_maxstack" INTEGER DEFAULT NULL,
    "diameter" INTEGER DEFAULT NULL,
    "diamonds" INTEGER DEFAULT NULL,
    "even_diamonds" INTEGER DEFAULT NULL,
    "odd_diamonds" INTEGER DEFAULT NULL,
    "girth" INTEGER DEFAULT NULL,
    "avg_degree" INTEGER DEFAULT NULL,
    "max_degree" INTEGER DEFAULT NULL,
    "min_degree" INTEGER DEFAULT NULL,
    "avg_indegree" INTEGER DEFAULT NULL,
    "max_indegree" INTEGER DEFAULT NULL,
    "min_indegree" INTEGER DEFAULT NULL,
    "avg_outdegree" INTEGER DEFAULT NULL,
    "max_outdegree" INTEGER DEFAULT NULL,
    "min_outdegree" INTEGER DEFAULT NULL,
    "avg_1_neighbourhood" INTEGER DEFAULT NULL,
    "min_1_neighbourhood" INTEGER DEFAULT NULL,
    "max_1_neighbourhood" INTEGER DEFAULT NULL,
    "avg_2_neighbourhood" INTEGER DEFAULT NULL,
    "min_2_neighbourhood" INTEGER DEFAULT NULL,
    "max_2_neighbourhood" INTEGER DEFAULT NULL,
    "avg_3_neighbourhood" INTEGER DEFAULT NULL,
    "min_3_neighbourhood" INTEGER DEFAULT NULL,
    "max_3_neighbourhood" INTEGER DEFAULT NULL,
    "sccs" INTEGER DEFAULT NULL,
    "scc_quotient_height" INTEGER DEFAULT NULL,
    "terminal_sccs" INTEGER DEFAULT NULL,
    "trivial_sccs" INTEGER DEFAULT NULL   
);
CREATE TABLE "generation" (
    "id" INTEGER PRIMARY KEY,
    "time" REAL,
    "tool" TEXT
);
CREATE TABLE "solving" (
    "id" INTEGER PRIMARY KEY,
    "time" REAL,
    "tool" TEXT,
    "solution" TEXT
);
CREATE TABLE "reduction" (
    "id" INTEGER PRIMARY KEY,
    "idfrom" INTEGER NOT NULL,
    "idto" INTEGER NOT NULL,
    "tool" TEXT,
    "time" REAL
);
CREATE VIEW "query_gamesizes" AS
SELECT cases.name,
       instances.name 'casename',
       games.reduction,
       gamesizes.*,
       gamesizes.vertices+gamesizes.edges 'size',
       gamesizes.sccs-gamesizes.trivial_sccs 'nontrivial_sccs',
       solving.time + reduction.time 'times'
FROM gamesizes, games, solving, cases, instances, reduction
WHERE gamesizes.id = games.id
  AND games.instance = instances.id
  AND cases.id = instances.caseid
  AND solving.id = games.id
  AND reduction.idto = games.id
'''

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
  SET even_vertices=?,
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
            (data.get('Graph',{}).get('Number of even vertices', None),
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
  

def loaddata(conn, data, datadir, caseid=None):
  if isinstance(data, list):
    for d in data:
      loaddata(conn, d, datadir)
  else:
    assert isinstance(data, dict)
    if caseid is None and data.has_key('case'):
      case=data['case']
      if data.has_key('properties'):
        type='modelchecking'
      elif data.has_key('instances'):
        if data['instances'][0].has_key('compact'):
          type='mlsolver'
        else:
          type='equivalence'
      else:
        type='pgsolver'
      
      c = conn.cursor()
      c.execute('INSERT INTO cases VALUES (null, ?, ?)', (case, type))
      caseid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      
      LOG.info("Added case with id {0}".format(caseid))
      
      if not data.has_key('properties') and not data.has_key('instances'):
        loaddata(conn, data, datadir, caseid)
        
      for property in data.get('properties', []):
        loaddata(conn, property, datadir, caseid)
      for instance in data.get('instances', []):
        loaddata(conn, instance, datadir, caseid)
          
    else:
      # Instance level
      name = data.get('property', None)
      if not name:
        name = data.get('compact')
      if not name:        
        name = data.get('equivalence')
      if not name:
        name = 'default'
      
      c = conn.cursor()
      c.execute('INSERT INTO instances VALUES (null, ?, ?)', (caseid, name))
      instanceid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      LOG.info("Added instance {0}".format(instanceid))
      
      equivalences = ['orig', 'bisim', 'fmib', 'stut', 'gstut']
      games = {}
      for reduction in equivalences:
        red = reduction
        if red == 'orig':
          red = 'original'
        yamlfile = data.get('files',{}).get(red, None)
        gmfile = os.path.splitext(yamlfile)[0].replace('/data/','/temp/') + '.gm'
        c.execute('INSERT INTO games VALUES (null, ?, ?, ?)', (instanceid, reduction, gmfile))
        games[reduction] = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      
      sizes = data['sizes']
      times = data['times']
      solutions = data['solutions']
      files = data['files']
      c.execute('INSERT INTO generation VALUES (?, ?, ?)', (games['orig'], data['generation'].get('times', {}).get('total', None), data['generation'].get('tool', None)))
      for reduction in equivalences:
        if reduction == 'orig':
          red = 'original'
        else:
          red = reduction
          
        c.execute('INSERT INTO gamesizes (id, vertices, edges) VALUES (?, ?, ?)', (games[reduction], sizes[reduction].get('vertices', None), sizes[reduction].get('edges', None)))
        if reduction != 'orig':
          c.execute('INSERT INTO reduction VALUES (null, ?, ?, ?, ?)', (games['orig'], games[reduction], 'pgconvert', times[reduction].get('reduction', {}).get('reduction', None)))
        else: # for efficient querying
          c.execute('INSERT INTO reduction VALUES (null, ?, ?, ?, ?)', (games['orig'], games['orig'], 'dummy', 0.0))
          
        solvingtime = times[red].get('pbespgsolve', {})
        if solvingtime == 'timeout':
          solvingtime = None
        else:
          solvingtime = solvingtime.get('solving', None)
        solution = solutions.get(red, {}).get('pbespgsolve', None)
        if solution == 'unknown':
          solution = None       
        c.execute('INSERT INTO solving VALUES (?, ?, ?, ?)', (games[reduction], solvingtime, 'pbespgsolve', solution))
        conn.commit()
        
        loaddetaildata(conn, games[reduction], files[red], datadir)
        conn.commit()
        
def run(resultfile, sqlitefile, initialise):
  conn = sqlite3.connect(sqlitefile)
  if initialise:
    conn.executescript(SCHEMA_QUERY)
    conn.commit()
  
  datadir = os.path.dirname(os.path.abspath(resultfile))
  data = yaml.load(open(resultfile, 'r'))
  
  loaddata(conn, data, datadir)
  
  conn.commit()  
  conn.close()

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] resultfile sqlitefile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  parser.add_option('-i', action='store_true', dest='initialise',
                    help='Intialise database with its schema.')
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
  
  run(resultfile, sqlitefile, options.initialise)

if __name__ == '__main__':
  runCmdLine()
