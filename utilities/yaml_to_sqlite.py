import logging
import optparse
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
    "case" INTEGER NOT NULL,
    "name" TEXT NOT NULL
);
CREATE TABLE "games" (
    "id" INTEGER PRIMARY KEY,
    "instance" INTEGER NOT NULL,
    "reduction" TEXT NOT NULL
);
CREATE TABLE "gamesizes" (
    "id" INTEGER PRIMARY KEY,
    "vertices" INTEGER NOT NULL,
    "edges" INTEGER NOT NULL
);
CREATE TABLE "generation" (
    "id" INTEGER PRIMARY KEY,
    "time" REAL NOT NULL,
    "tool" TEXT NOT NULL
);
CREATE TABLE "solving" (
    "id" INTEGER PRIMARY KEY,
    "time" REAL NOT NULL,
    "tool" TEXT NOT NULL,
    "solution" TEXT NOT NULL
);
CREATE TABLE "reduction" (
    "id" INTEGER PRIMARY KEY,
    "idfrom" INTEGER NOT NULL,
    "idto" INTEGER NOT NULL,
    "tool" TEXT NOT NULL,
    "time" REAL NOT NULL
);'''

def loaddata(conn, data, caseid=None):
  if isinstance(data, list):
    for d in data:
      loaddata(conn, d)
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
        loaddata(conn, data, caseid)
        
      for property in data.get('properties', []):
        loaddata(conn, property, caseid)
      for instance in data.get('instances', []):
        loaddata(conn, instance, caseid)
          
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
      print caseid
      print data
      c.execute('INSERT INTO instances VALUES (null, ?, ?)', (caseid, name))
      instanceid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      LOG.info("Added instance {0}".format(instanceid))
      
      equivalences = ['orig', 'bisim', 'fmib', 'stut', 'gstut']
      games = {}
      for reduction in equivalences:
        c.execute('INSERT INTO games VALUES (null, ?, ?)', (instanceid, reduction))
        games[reduction] = c.execute('SELECT last_insert_rowid()').fetchone()[0]
      
      sizes = data['sizes']
      times = data['times']
      solutions = data['solutions']
      c.execute('INSERT INTO generation VALUES (?, ?, ?)', (games['orig'], data['generation']['times']['total'], data['generation']['tool']))
      for reduction in equivalences:
        c.execute('INSERT INTO gamesizes VALUES (?, ?, ?)', (games[reduction], int(sizes[reduction]['vertices']), int(sizes[reduction]['edges'])))
        if reduction != 'orig':
          c.execute('INSERT INTO reduction VALUES (null, ?, ?, ?, ?)', (games['orig'], games[reduction], 'pgconvert', times[reduction]['reduction']['reduction']))
        if reduction == 'orig':
          red = 'original'
        else:
          red = reduction
        c.execute('INSERT INTO solving VALUES (?, ?, ?, ?)', (games[reduction], times[red]['pbespgsolve']['solving'], 'pbespgsolve', solutions[red]['pbespgsolve']))
        
        
        
        

def run(resultfile, sqlitefile):
  conn = sqlite3.connect(sqlitefile)
  conn.executescript(SCHEMA_QUERY)
  conn.commit()
    
  data = yaml.load(open(resultfile, 'r'))
  
  loaddata(conn, data)
  
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
  
  run(resultfile, sqlitefile)

if __name__ == '__main__':
  runCmdLine()