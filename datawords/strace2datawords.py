from __future__ import print_function
import sys

from posix_omni_parser import Trace




class DataWord:
  def __init__(self, system_call, captured_arguments, predicate_results):
    self.original_system_call = system_call
    self.captured_arguments = captured_arguments
    self.predicate_results = predicate_results


  def get_dataword(self):
    tmp = ''
    for i in self.predicate_results:
      if i:
        tmp += '[T]'
      else:
        tmp += '[F]'
    tmp += self.original_system_call.name
    tmp += '('
    tmp += ', '.join(self.captured_arguments)
    tmp += ')'
    return tmp




class Preamble:
  def __init__(self):
    self.predicates = {}
    self.captures = {}
    self._current_captured_args = None
    self._current_predicate_results = None
    self._current_syscall = None


  def handle_syscall(self, call):
    self._current_syscall = call
    self._current_captured_args = {}
    self._current_predicate_results = []
    self._capture_args()
    self._apply_predicates()
    return DataWord(self._current_syscall, self._current_captured_args, self._current_predicate_results)


  def _apply_predicates(self):
    for i in self.predicates[self._current_syscall.name]:
      self._current_predicate_results.append(i(self._current_captured_args))


  def _capture_args(self):
    for i in self.captures[self._current_syscall.name]:
      self._current_captured_args[i["arg_name"]] = {
        "arg_pos": i["arg_pos"],
        "value": self._current_syscall.args[i["arg_pos"]] if i["arg_pos"] != "ret" else self._current_syscall.ret[0]}


  def capture(self, syscall_name, arg_name, arg_pos):
    if syscall_name not in self.captures:
      self.captures[syscall_name] = []
    self.captures[syscall_name].append({"arg_name": arg_name, "arg_pos": arg_pos})


  def predicate(self, syscall_name, f):
    if syscall_name not in self.predicates:
      self.predicates[syscall_name] = []
    self.predicates[syscall_name].append(f)



if __name__ == "__main__":
  t = Trace.Trace(sys.argv[1], "./syscall_definitions.pickle")

  pre = Preamble()
  pre.predicate("open", lambda args: args["filename"]["value"].value == "\"test.txt\"")
  pre.capture("open", "filename", 0)

  pre.predicate("read", lambda args: args["result"]["value"] == 10)
  pre.capture("read", "result", "ret")

  for i in t.syscalls:
    print(pre.handle_syscall(i).captured_arguments)

