from ply import lex
from ply import yacc
from register_automaton import RegisterAutomaton
from register_automaton import State
from register_automaton import Transition
from strace2datawords import Preamble
from strace2datawords import DataWord
import pickle
import os
import sys


class CSlangError(Exception):
  pass


reserved = {
    'capture' : 'CAPTURE',
    'predicate' : 'PREDICATE',
    'as' : 'AS',
    'ret' : 'RET'
}

tokens = ["IDENTIFIER",
          "LPAREN",
          "READOP",
          "WRITEOP",
          "EQUALSOP",
          "ASSIGN",
          "NUMERIC",
          "ASSIGNVALUE",
          "PARAMSEP",
          "RPAREN",
          "SEMI"
] + list(reserved.values())


t_LPAREN = r"\("
t_READOP = r"\?"
t_WRITEOP= r"\!"
t_EQUALSOP = r"=="
t_ASSIGN = r"<-"
t_NUMERIC = r"[0-9][0-9]*"
t_ASSIGNVALUE = "\".*\""
t_RPAREN = r"\)"
t_PARAMSEP = r",[\s]*"
t_SEMI = r";"
t_ignore = " \t\n"

# We use a function to define this function for two reasons:
# 1. Ply gives tokens defined by functions higher priority meaning this
# rule will be used for ambiguous stuff that could be an identifier or
# could be a keyword.
# 2. We can define logic to figure out if something is a keyword rather
# than an identifier and return the appropriate type
def t_IDENTIFIER(t):
  r"[A-Za-z_][a-zA-Z0-9]*"
  t.type = reserved.get(t.value, 'IDENTIFIER')
  return t

def t_error(t):
  pass

def t_COMMENT(t):
  r'\#.*'

lexer = lex.lex()

automaton = RegisterAutomaton()
preamble = Preamble()
in_preamble = True

def p_error(p):
  print("Error with:")
  print(p)

def p_expressionlist(p):
  ''' expressionlist : expression  expressionlist
                     | expression
  '''

def p_expression(p):
  ''' expression : dataword SEMI
                 | registerassignment SEMI
                 | capturestmt SEMI
                 | predicatestmt SEMI
  '''


def p_capturestmt(p):
  ''' capturestmt : CAPTURE IDENTIFIER NUMERIC AS IDENTIFIER
                  | CAPTURE IDENTIFIER RET AS IDENTIFIER
  '''


  global in_preamble
  if in_preamble:
    if p[3] == "ret":
      preamble.capture(p[2], p[5], "ret")
    else:
      preamble.capture(p[2], p[5], p[3])
  else:
    raise CSlangError("Found capture statement after preamble processing has ended")


def p_predicatestmt(p):
  ''' predicatestmt : PREDICATE IDENTIFIER IDENTIFIER EQUALSOP ASSIGNVALUE '''

  global in_preamble
  if in_preamble:
    preamble.predicate(p[2], lambda args: args[p[3]]["value"].value == p[5])
  else:
    raise CSlangError("Found predicate statement after preamble processing has ended")


def p_registerassignment(p):
  ''' registerassignment : IDENTIFIER ASSIGN ASSIGNVALUE
  '''

  global in_preamble
  in_preamble = False
  print(in_preamble)
  automaton.registers[p[1]] = p[3]


def p_dataword(p):
  ''' dataword : IDENTIFIER LPAREN parameterlist RPAREN
  '''

  global in_preamble
  in_preamble = False
  register_matches = []
  register_stores = []
  for i, v in enumerate(p[3]):
    if v[0] == "?":
      # When we see the "?" operator it means in order to get into this state,
      # the register name following "?" needs to have the same value as the
      # captured argument in the same position in the data word.  For example:
      #
      # open(?filedesc);
      #
      # means that in order to transition to the next state, the current
      # dataword must represent an open system call with captured argument 0
      # matching the value in the filedesc register.  Captured argument order
      # is important and comes from the order the captures are specified in the
      # preamble
      register_matches.append((i, v[1:]))
    if v[0] == "!":


      # When we see "!" it means take the value from the captured argument
      # corresponding to this parameter's position in the current dataword and
      # store it into the following register value.  We do this by specifying
      # register_store tuple that looks like (<captured_arg_position>,
      # <register_value>).  These register stores are performed whenever we
      # transition into a new state so we give them to the new State being
      # created below
      register_stores.append((i, v[1:]))

  # We encountered a new dataword so we make a new state
  automaton.states.append(State(p[1], register_stores=register_stores))

  # We create a transition to this state on the previous state
  automaton.states[-2].transitions.append(Transition(p[1],
                                          register_matches,
                                          len(automaton.states) - 1))


def p_parameterlist(p):
  '''parameterlist : parameter PARAMSEP parameterlist
                   | parameter
  '''

  if len(p) == 4:
    p[0] = [p[1]] + p[3]
  else:
    p[0] = [p[1]]



def p_parameter(p):
  '''parameter : READOP IDENTIFIER
               | WRITEOP IDENTIFIER
               | IDENTIFIER
  '''
  if len(p) == 3:
    p[0] = p[1] + p[2]
  else:
    p[0] =  p[1]



parser = yacc.yacc()
basename = os.path.splitext(os.path.basename(sys.argv[1]))[0]
with open(sys.argv[1], "r") as f:
  parser.parse(f.read())
with open(basename + ".auto", "w") as f:
  pickle.dump(automaton, f)





# This is to parse the program that is going to read the datawords that will be incoming from the preprocessor
# each dataword parsed defines the transition requirements from the current state to the next
#  the datawords being generated will have data in them.  The program will only have identifiers
# This thing needs to generate instructions or whatever to do the transitioning and reading registers and all that
# output an automaton object



# The "choice" operatior "|" would be a case where we have a branch in the automaton.
