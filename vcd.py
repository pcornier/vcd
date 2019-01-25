#!/usr/bin/python
import logging
import sys, re, readline, pickle
from pyparsing import *

logging.basicConfig(level=logging.INFO)

def main(argv):

  fh = None
  source = ''

  if len(argv) > 0:
    fp = argv[0]

    try:
      fh = open(fp, 'r')
      source = fh.read()

    except IOError:
      print('Cannot open', fp)
      sys.exit(2)

  vcd = VCD(fh, source)
  
  readline.parse_and_bind("tab: complete")
  vcd.prompt()
  sys.exit()

class VCD():

  signals = [] 
  timescale = 1  
  active_scope = []  
  active_time = 0  
  waves = {} 
  max_time = 0 
  time_start = 0
  time_length = 50
  fh = None

  def openScope(self, tokens):
    logging.info('open scope')
    logging.info(tokens)
    self.active_scope.append(tokens.name)

  def closeScope(self, tokens):
    logging.info('close scope')
    logging.info(tokens)
    self.active_scope.pop()

  def setVariable(self, tokens):
    logging.info('set variable')
    logging.info(tokens)
    _id = tokens.id
    self.waves[_id] = {
      'id': _id,
      'type': tokens.type,
      'size': tokens.size,
      'name': tokens.name,
      'scope': self.active_scope.copy(),
      'history': {}
    }

  def setValueVar(self, time, _id, value, typ):
    value = list(value)
    if _id == '':
        _id = value[1]
        value = value[0]
    if _id in self.waves:
      if not typ or typ == 'b':
        if 'z' in value or 'x' in value:
          if len(value) > 1:
            self.waves[_id]['history'][time] = ''.join(value)
          else:
            self.waves[_id]['history'][time] = None
        else:
          self.waves[_id]['history'][time] = int(''.join(value), 2)
      elif typ == 's':
        self.waves[_id]['history'][time]= ''.join(value)
      
      logging.info(f't:{time} id:{_id} val:' + str(self.waves[_id]['history'][time]))


  def setTime(self, tokens):
    logging.info('set time')
    logging.info(tokens)
    self.active_time = int(tokens.time)
    if self.active_time > self.max_time:
      self.max_time = self.active_time

  def setValue(self, tokens):
    logging.info('set value')
    logging.info(tokens)
    self.setValueVar(self.active_time, tokens.id, tokens.value, tokens.type)

  def setDate(self, tokens):
    logging.info('set date')
    logging.info(tokens)

  def setVersion(self, tokens):
    logging.info('set version')
    logging.info(tokens)

  def setTimescale(self, tokens):
    logging.info('set timescale')
    logging.info(tokens)
    self.timescale = int(tokens.timescale)

  def parse(self, source):

		  ## VCD grammar

		  self.waves = {}
		  self.max_time = 0
		  self.active_time = 0

		  end = Keyword('$end')
		  date = ('$date' + OneOrMore(Word(alphanums + ':,'))('date') + end).setParseAction(self.setDate)
		  version = ('$version' + SkipTo(end) + end).setParseAction(self.setVersion)
		  comment = '$comment' + SkipTo(end) + end
		  tscale = ('$timescale' + Word(nums)('timescale') + oneOf('fs ps ns us ms s') + end).setParseAction(self.setTimescale)
		  open_scope = '$scope'
		  scope_type = oneOf('begin fork function module task')
		  scope_name = Word(alphanums + '_')('name')
		  scope = (open_scope + scope_type + scope_name + end).setParseAction(self.openScope)
		  open_var = '$var'
		  var_type = oneOf('event integer parameter real realtime reg supply0 supply1 time tri triand trior trireg tri0 tri1 wand wire wor')('type')
		  var_size = Word(nums)('size')
		  var_id = Word(printables)('id')
		  var_name = Word(alphanums + '_[]:')('name')
		  variable = (open_var + var_type + var_size + var_id + var_name + end).setParseAction(self.setVariable)
		  close_scope = (Literal('$upscope') + end).setParseAction(self.closeScope)
		  definitions = OneOrMore(scope ^ variable ^ close_scope) + Literal('$enddefinitions').setParseAction(lambda: logging.info('end definitions')) + end
		  typid = Optional(oneOf('b B r R'))('type')
		  bval = Combine(OneOrMore(oneOf('0 1 z x Z X'))('value')  + Optional(' ') + SkipTo(White())('id')) + White()
		  sval = Combine(Word('s')('type') + Word(alphanums+'_')('value')) + Word(printables)('id')
		  sim_val = ((typid + bval) | sval).setParseAction(self.setValue)
		  dumps = oneOf('$dumpvars $dumpall $dumpoff $dumpon') + OneOrMore(sim_val) + end
		  time = Combine('#' + Word(nums)('time')).setParseAction(self.setTime)
		  vcd = OneOrMore(date ^ version ^ tscale ^ comment) + definitions + OneOrMore(dumps ^ time ^ sim_val)
		  vcd.parseString(source, parseAll=True)
		  

  def listAllSignals(self, asList = False):
    slist = []
    for i,w in self.waves.items():
      key = ':'.join(w['scope']) + ':' + w['name']
      if key in self.signals:
        key = '->' + key
      slist.append(key)
    nl = '\n' if asList else ' '
    print(f'Signals:\n{nl.join(slist)}')

  def __init__(self, fh, source):
    self.fh = fh

    if source != '':
      self.parse(source)

  def printSignals(self):

    if len(self.signals) == 0:
      print('no signals')
      return

    # select corresponding waves
    selected = []
    for i,w in self.waves.items():
      key = ':'.join(w['scope']) + ':' + w['name']
      if key in self.signals:
        selected.append(w)

    # todo rename
    # helper that returns a printable char from a waveform at specific time
    def getChar(t, w):
      if not t in w['history']:
        # get first t
        p = next(iter(w['history']))
        # search for previous time
        for i,ht in enumerate(w['history']):
          if ht >= t:
            # found
            return getChar(p, w)
          if i == len(w['history'])-1:
            # end of history
            return getChar(ht, w)
          p = ht
        return '\u2015', 'z'
      v = w['history'][t]
      if w['size'] == '1':
        try:
          v = int(v)
          if v == 1:
            return '\u203e', '\u203e' if t == 0 else '/\u203e'
          else:
            return '_', '_' if t == 0 else '\_'
        except ValueError:
          return ' ', '\u2573 '+str(v)
      try:
        v = int(v)
        return ' ', '\u2573 '+hex(v)
      except ValueError:
        return ' ', '\u2573 '+str(v)

    # generate waves
    rows = []
    timer = ' ' * self.time_length
    for w in selected:
      value, prt = getChar(self.time_start, w)
      row = ''
      for t in range(self.time_start, self.time_start + self.time_length, self.timescale):
        if t in w['history']:
          value, prt = getChar(t, w)
          s = t - self.time_start
          # if s + len(prt) > self.time_length:
          #   prt = prt[0:len(prt)-(s+len(prt)-self.time_length)-1]
          row = row[0:s] + prt
          timer = timer[0:s] + str(t) + timer[min(s+len(str(t)), self.time_start + self.time_length):]
        else:
          if len(row) + len(value) < self.time_length:
            row += value
      row = ('\u001b[7m' if int(w['size']) > 1 or w['type'] == 'real' else '') + row + '\u001b[0m'
      rows.append(f"{w['name'][:5]:<5}: {row}")

    # print
    print(f'\n       {timer}')
    for r in rows:
      print('\n'+r)
    print('\n')

  # TODO: migrate to a REPL python package
  def prompt(self):
    cmd = input('> ')
    if cmd == 'q':
      sys.exit(0)
    elif cmd == 'help':
      print('help:')
    #elif cmd .startswith('t'):
    #  r = re.search('(\d+)', cmd[1:])
    #  if r and r.group(1):
    #    self.timescale = int(r.group(1))
    elif cmd == 'f':
      self.time_start = min(self.max_time, self.time_start+5)
      self.printSignals()
    elif cmd == 'p':
      self.printSignals()
    elif cmd == 'sc':
      with open('signals.conf', 'wb') as f:
        pickle.dump(self.signals, f)
      print('saved signal configuration')
    elif cmd == 'lc':
      with open('signals.conf', 'rb') as f:
        self.signals = pickle.load(f)
      print('loaded signal configuration')
    elif cmd == 'r':
      if self.fh:
        self.fh.seek(0)
        self.parse(self.fh.read())
        print('reloaded')
      else:
        print('no file loaded')
    elif cmd.startswith('r'):
      r = re.search('(\d+)\s+(\d+)', cmd)
      if r:
        if r.group(1):
          self.time_start = int(r.group(1))
        if r.group(2):
          self.time_length = int(r.group(2))
      self.printSignals()
    elif cmd == 's':
      self.listAllSignals()
    elif cmd == 'ss':
      self.listAllSignals(True)
    elif cmd == 'aa':
      for i, w in self.waves.items():
        key = ':'.join(w['scope']) + ':' + w['name']
        self.signals.append(key)
      print('added all signals')
    elif cmd.startswith('a'):
      new = list(filter(None, cmd[1:].split(' ')))
      for n in new:
        self.signals.append(n)
      print('signals added')
    elif cmd == 'da':
      self.signals = []
      print('deleted all signals from selection')
    elif cmd.startswith('l'):
      r = re.search('([^\s]+)', cmd[1:])
      if r:
        if r.group(1):
          try:
            self.fh = open(r.group(1), 'r')
            self.parse(self.fh.read())
            print('loaded')
          except:
            print('error while parsing file')
    elif cmd.startswith('d'):
      r = re.search('((\w+).*)+', cmd)
      print(r)
      # todo remove specific
    elif cmd == '':
      pass
    else:
      print('unknown command', cmd)
    self.prompt()


if __name__ == '__main__':
    main(sys.argv[1:])
