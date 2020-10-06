class RegisterAutomaton:
  def __init__(self):
    self.states = []
    self.states.append(State("startstate"))
    self.current_state = 0
    self.registers = {}


  def __str__(self):
    tmp = ""
    tmp += "Automaton:\n"
    tmp += "  Current State: " + str(self.current_state) + "\n"
    for i in self.states:
      tmp += "  State:\n" + str(i) + "\n"
    return tmp


  def match(self, incoming_dataword):
    to_state = self.states[self.current_state].match(incoming_dataword, self.registers)
    if to_state != -1:
      self.current_state = to_state
      # We've moved into a new state so we need to "enter" it.
      # This executes the register store operations required by the new state
      self.states[self.current_state].enter(incoming_dataword, self.registers)


  def is_accepting(self):
    return self.states[self.current_state].is_accepting


class State:
  def __init__(self, name, transitions=None, is_accepting=False, register_stores=None, register_writes=None, tags=None):
    self.name = name
    self.transitions = transitions if transitions is not None else []
    self.is_accepting = is_accepting
    self.register_stores = register_stores if register_stores is not None else []
    self.register_writes = register_writes if register_writes is not None else []
    self.tags = tags if tags is not None else []

  def match(self, incoming_dataword, registers):
    for i in self.transitions:
      to_state = i.match(incoming_dataword, registers)
      if to_state != -1:
        return to_state
    return -1

  def enter(self, incoming_dataword, registers):
    # incoming_dataword brought us into this state so its time to execute
    # our register stores using the captured_arguments it contains
    for i in self.register_stores:
      for j in range(len(incoming_dataword.captured_arguments)):
        # We have to search through a list of dictionaries until we find
        # one whose "arg_name" matches the arg_name from the register match
        # tuple (position 0)
        if incoming_dataword.captured_arguments[j]["arg_name"] == i[0]:
          cca = incoming_dataword.captured_arguments[j]
      registers[i[1]] = str(cca["members"][0])

    for i in self.register_writes:
      cca = incoming_dataword
      # HACK: THIS WAS COPIED FROM AROUND LINE 52! REFACTOR OUT!
      for j in range(len(incoming_dataword.captured_arguments)):
        # We have to search through a list of dictionaries until we find
        # one whose "arg_name" matches the arg_name from the register match
        # tuple (position 0)
        if incoming_dataword.captured_arguments[j]["arg_name"] == i[0]:
          cca = incoming_dataword.captured_arguments[j]
      cca["members"][0] = registers[i[1]]


  def __str__(self):
    tmp = ""
    tmp += "    Name: " + self.name + "\n"
    tmp += "    Tags: "
    for i in self.tags:
      tmp += i
    tmp += "\n"
    for i in self.transitions:
      tmp += "      Transition:\n" + str(i) + "\n"
    return tmp


class Transition:
  def __init__(self, dataword_name, register_matches, to_state):
    self.dataword_name = dataword_name
    self.register_matches = register_matches
    self.to_state = to_state

  def __str__(self):
    tmp = ""
    tmp += "        dataword_name: " + self.dataword_name + "\n"
    tmp += "        register_matches: " + str(self.register_matches) + "\n"
    tmp += "        to_state: " + str(self.to_state) + "\n"
    return tmp

  def match(self, current_dataword, registers):
    if current_dataword.get_name() == self.dataword_name and self._pass_register_matches(current_dataword, registers):
      return self.to_state
    return -1

  def _pass_register_matches(self, incoming_dataword, registers):
    for i in self.register_matches:
      # HACK: THIS WAS COPIED FROM AROUND LINE 52! REFACTOR OUT!
      for j in range(len(incoming_dataword.captured_arguments)):
        # We have to search through a list of dictionaries until we find
        # one whose "arg_name" matches the arg_name from the register match
        # tuple (position 0)
        if incoming_dataword.captured_arguments[j]["arg_name"] == i[0]:
          cca = incoming_dataword.captured_arguments[j]
      if str(cca["members"][0]) != registers[str(i[1])]:
        return False
    return True


# Matching with no registers -> Does the current data word name match the data
# word name specified by one of the transitions Right now we only go forward in
# transitions, so transitioning is current_state++
# Each state only has one transition
