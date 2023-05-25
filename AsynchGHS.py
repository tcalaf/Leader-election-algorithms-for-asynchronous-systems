from simgrid import Engine, this_actor, Mailbox, Comm
import random
from enum import Enum
import sys
from dataclasses import dataclass

INF = 100

class NodeState(Enum):
  SLEEPING = 0
  FIND = 1
  FOUND = 2

class EdgeState(Enum):
  BASIC = 0
  BRANCH = 1
  REJECTED = 2

@dataclass
class Edge:
  dNode: int
  weight: int
  state: EdgeState

  @property
  def toString(self):
    return "(N: " + str(self.dNode) + ", W: " + str(self.weight) + ", T: " + str(self.state.name) + ")"

class MessageType(Enum):
  CONNECT = 0
  INITIATE = 1
  TEST = 2
  REPORT = 3
  ACCEPT = 4
  REJECT = 5
  CHANGE_ROOT = 6
  TERMINATE = 7

@dataclass
class Message:
  source: int
  msg_type: MessageType

class ConnectMessage(Message):
  def __init__(self, source: int, level: int):
      super().__init__(source=source, msg_type=MessageType.CONNECT)
      self.level = level

  def toString(self):
    return f"Level = {self.level}"

class InitiateMessage(Message):
  def __init__(self, source: int, level: int, fragment_id: int, state: int):
      super().__init__(source=source, msg_type=MessageType.INITIATE)
      self.level = level
      self.fragment_id = fragment_id
      self.state = state

  def toString(self):
    return f"Level = {self.level}, Fragment id = {self.fragment_id}, State = {self.state}"

class TestMessage(Message):
  def __init__(self, source: int, level: int, fragment_id: int):
      super().__init__(source=source, msg_type=MessageType.TEST)
      self.level = level
      self.fragment_id = fragment_id

  def toString(self):
    return f"Level = {self.level}, Fragment id = {self.fragment_id}"

class ReportMessage(Message):
  def __init__(self, source: int, best_wt: int):
      super().__init__(source=source, msg_type=MessageType.REPORT)
      self.best_wt = best_wt

  def toString(self):
    return f"Best weight = {self.best_wt}"

class AcceptMessage(Message):
  def __init__(self, source: int):
      super().__init__(source=source, msg_type=MessageType.ACCEPT)

class RejectMessage(Message):
  def __init__(self, source: int):
      super().__init__(source=source, msg_type=MessageType.REJECT)

class ChangeRootMessage(Message):
  def __init__(self, source: int):
      super().__init__(source=source, msg_type=MessageType.CHANGE_ROOT)

class TerminateMessage(Message):
  def __init__(self, source: int, leader: int):
      super().__init__(source=source, msg_type=MessageType.TERMINATE)
      self.leader = leader
  def toString(self):
    return f"Leader = {self.leader}"

class Node:
  def print_adjacent_edges(self):
    msg = ""
    for e in self.adjacent_edges:
      msg += e.toString + " "
    this_actor.info(f"My adjacent edges are: {msg}")

  def get_adjacent_edges(self, links):
    adjacent_edges = []
    for neighbour, distance in enumerate(links):
      if int(distance) > 0:
        adjacent_edges.append(Edge(dNode = int(neighbour), weight = int(distance), state = EdgeState.BASIC))
    self.adjacent_edges = adjacent_edges

  def get_edge_by_dNode(self, dNode):
    for edge in self.adjacent_edges:
      if edge.dNode == dNode:
        return edge

  # procedure wakeup
  def wakeup(self):
    # Let m be adjacent edge of minimum weight
    m = min(self.adjacent_edges, key = lambda x: x.weight)
    this_actor.debug(f"Minimum adjacent edge is: " + m.toString)

    # SE(m) <- Branch
    m.state = EdgeState.BRANCH
    this_actor.info(f"[BRANCH to {m.dNode}] () : {{}}")

    # LN <- 0
    self.level = 0

    # SN <- Found
    self.state = NodeState.FOUND

    # Find-count <- 0
    self.find_count = 0

    # Send Connect(O) on edge m
    mailboxTo = Mailbox.by_name(str(m.dNode))
    payload = ConnectMessage(source = self.id, level = self.level)
    payload_size_in_bytes = sys.getsizeof(payload)
    comm = mailboxTo.put_async(payload, payload_size_in_bytes)
    self.pending_comms.append(comm)
    this_actor.info(f"[{MessageType.CONNECT.name} to {m.dNode}] ({self.id} -- Connect --> {m.dNode}) : {{{payload.toString()}}}")
    #this_actor.info(self.toString())

  # procedure report
  def report(self):
    # if find-count = 0 and test-edge = nil 
    if self.find_count == 0 and self.test_edge is None:
      # SN <- Found
      self.state = NodeState.FOUND
      # send Report(best-wt) on in-branch
      mailboxTo = Mailbox.by_name(str(self.in_branch.dNode))
      payload = ReportMessage(source = self.id, best_wt = self.best_wt)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.REPORT.name} to {self.in_branch.dNode}] ({self.id} -- Report --> {self.in_branch.dNode}) : {{{payload.toString()}}}")
      #this_actor.info(self.toString())
      
  # procedure test
  def test(self):
    basic_adjacent_edges = [edge for edge in self.adjacent_edges if edge.state == EdgeState.BASIC]
    this_actor.info(f"Basic adjacent edges nr: {len(basic_adjacent_edges)}")
    # If there are adjacent edges in the state Basic
    if len(basic_adjacent_edges) > 0:
      # test-edge <- the minimum-weight adjacent edge in state Basic;
      self.test_edge = min(basic_adjacent_edges, key = lambda x: x.weight)
      this_actor.info(f"Min Basic adjacent edge: {self.test_edge}")
      # send Test(LN, FN) on test-edge
      mailboxTo = Mailbox.by_name(str(self.test_edge.dNode))
      payload = TestMessage(source = self.id, level = self.level, fragment_id = self.fragment_id)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.TEST.name} to {self.test_edge.dNode}] ({self.id} -- Test --> {self.test_edge.dNode}) : {{{payload.toString()}}}")
      #this_actor.info(self.toString())
      
    else:
      # test-edge <- nil
      self.test_edge = None
      # execute procedure report
      self.report()

  # procedure change-root
  def change_root(self):
    # if SE(best-edge) = Branch
    this_actor.info("ChangeRoot" + self.toString())
    if self.best_edge.state == EdgeState.BRANCH:
      # send Change-root on best-edge
      mailboxTo = Mailbox.by_name(str(self.best_edge.dNode))
      payload = ChangeRootMessage(source = self.id)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.CHANGE_ROOT.name} to {self.best_edge.dNode}] ({self.id} -- Change Root --> {self.best_edge.dNode}) : {{}}")
      #this_actor.info(self.toString())
      
    # else
    else:
      # send Connect(LN) on best-edge;
      mailboxTo = Mailbox.by_name(str(self.best_edge.dNode))
      payload = ConnectMessage(source = self.id, level = self.level)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.CONNECT.name} to {self.best_edge.dNode}] ({self.id} -- Connect --> {self.best_edge.dNode}) : {{{payload.toString()}}}")
      #this_actor.info(self.toString())
      
      # SE(best-edge) <- Branch
      self.best_edge.state = EdgeState.BRANCH
      this_actor.info(f"[BRANCH to {self.best_edge.dNode}] () : {{}}")

  # Response to receipt of Connect(L) on edge j
  def handleConnect(self, msg):
    this_actor.info(f"[{MessageType.CONNECT.name} from {msg.source}] ({self.id} <-- Connect -- {msg.source}) : {{{msg.toString()}}}")
    #this_actor.info(self.toString())
      
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
 
    # If L < LN (ABSORPTION)
    if msg.level < self.level:
      # SE(j) <- Branch
      j.state = EdgeState.BRANCH
      this_actor.info(f"[BRANCH to {j.dNode}] () : {{}}")

      # Send Initiate(LN, FN, SN) on edge j
      mailboxTo = Mailbox.by_name(str(msg.source))
      payload = InitiateMessage(source = self.id, level = self.level, fragment_id = self.fragment_id, state = self.state)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.INITIATE.name} to {msg.source}] ({self.id} -- Initiate --> {msg.source}) : {{{payload.toString()}}}")
      #this_actor.info(self.toString())

      # if SN = Find
      if self.state == NodeState.FIND:
        # find-count <- find-count + 1
        self.find_count += 1

    # Else if SE(j) = Basic (Wait for the situation to change)
    elif j.state == EdgeState.BASIC:
      # Place received message at the end of queue
      mailboxTo = Mailbox.by_name(str(self.id))
      payload_size_in_bytes = 0
      comm = mailboxTo.put_async(msg, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[Place received {MessageType.CONNECT.name} message from {msg.source} at the end of queue!] () : {{}}")
      #this_actor.info(self.toString())
      
    # (MERGE) The fragment receving the Connect has also sent a Connect to the other fragment.
    else:
      # Send Initiate(LN + 1, w(j), Find) on edge j
      mailboxTo = Mailbox.by_name(str(msg.source))
      payload = InitiateMessage(source = self.id, level = self.level + 1, fragment_id = j.weight, state = NodeState.FIND)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.INITIATE.name} to {msg.source}] ({self.id} -- Initiate --> {msg.source}) : {{{payload.toString()}}}")
      #this_actor.info(self.toString())
      
  # Response to receipt of Initiate (L, F, S) on edge j
  def handleInitiate(self, msg):
    this_actor.info(f"[{MessageType.INITIATE.name} from {msg.source}] ({self.id} <-- Initiate -- {msg.source}) : {{{msg.toString()}}}")
    #this_actor.info(self.toString())
      
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)

    # LN <- L
    self.level = msg.level

    # FN <- F
    self.fragment_id = msg.fragment_id

    # SN <- S
    self.state = msg.state

    # in-branch <- j
    self.in_branch = j

    # best-edge <- nil
    self.best_edge = None

    # best-wt <- inf
    self.best_wt = INF

    for edge in self.adjacent_edges:
      # for all i ≠ j such that SE(i) = Branch
      if edge != j and edge.state == EdgeState.BRANCH:
        # send Initiate(L, F, S) on edge i
        mailboxTo = Mailbox.by_name(str(edge.dNode))
        payload = InitiateMessage(source = self.id, level = msg.level, fragment_id = msg.fragment_id, state = msg.state)
        payload_size_in_bytes = sys.getsizeof(payload)
        comm = mailboxTo.put_async(payload, payload_size_in_bytes)
        self.pending_comms.append(comm)
        this_actor.info(f"[{MessageType.INITIATE.name} to {edge.dNode}] ({self.id} -- Initiate --> {edge.dNode}) : {{{payload.toString()}}}")
        #this_actor.info(self.toString())
      
        # if S = Find
        if msg.state == NodeState.FIND:
          # find-count <- find-count + 1
          self.find_count += 1

    # if S = Find
    if msg.state == NodeState.FIND:
      # execute procedure test
      self.test()

  # Response to receipt of Test(L, F) on edge j
  def handleTest(self, msg):
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
    this_actor.info(f"[{MessageType.TEST.name} from {j.dNode}] ({self.id} <-- Test -- {j.dNode}) : {{{msg.toString()}}}")
    #this_actor.info(self.toString())
      
    # If L > LN
    if msg.level > self.level:
      # Place received message at the end of queue
      mailboxTo = Mailbox.by_name(str(self.id))
      payload_size_in_bytes = 0
      comm = mailboxTo.put_async(msg, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[Place received {MessageType.TEST.name} message from {msg.source} at the end of queue!] () : {{}}")
      #this_actor.info(self.toString())
      
    # else if F != FN
    elif msg.fragment_id != self.fragment_id:
      # send Accept on edge j
      mailboxTo = Mailbox.by_name(str(j.dNode))
      payload = AcceptMessage(source = self.id)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.ACCEPT.name} to {j.dNode}] ({self.id} -- Accept --> {j.dNode}) : {{}}")
      #this_actor.info(self.toString())
      
    else: # same fragment
      # if SE(j) = Basic
      if j.state == EdgeState.BASIC:
        # SE(j) = Rejected
        j.state = EdgeState.REJECTED
        this_actor.info(f"[REJECTED to {j.dNode}] () : {{}}")
      # if test-edge != j 
      if self.test_edge != j:
        # send Reject on edge j
        mailboxTo = Mailbox.by_name(str(j.dNode))
        payload = RejectMessage(source = self.id)
        payload_size_in_bytes = sys.getsizeof(payload)
        comm = mailboxTo.put_async(payload, payload_size_in_bytes)
        self.pending_comms.append(comm)
        this_actor.info(f"[{MessageType.REJECT.name} to {j.dNode}] ({self.id} -- Reject --> {j.dNode}) : {{}}")
        #this_actor.info(self.toString())
      
      else:
        # execute procedure test
        self.test()

  # Response to receipt of Report(w) on edgej
  def handleReport(self, msg):
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
    this_actor.info(f"[{MessageType.REPORT.name} from {j.dNode}] ({self.id} <-- Report -- {j.dNode}) : {{{msg.toString()}}}")
    this_actor.info(self.toString())  

    # if j != in-branch 
    if j != self.in_branch:
      # find-count <- find-count - 1
      self.find_count -= 1
      # if w < best-wt
      if msg.best_wt < self.best_wt:
        # best-wt <- w
        self.best_wt = msg.best_wt
        # best-edge <- j
        self.best_edge = j
      # execute procedure report
      self.report()
    # else if SN = Find
    elif self.state == NodeState.FIND:
      # place received message on end of queue
      mailboxTo = Mailbox.by_name(str(self.id))
      payload_size_in_bytes = 0
      comm = mailboxTo.put_async(msg, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[Place received {MessageType.REPORT.name} message from {msg.source} at the end of queue!] () : {{}}")
      #this_actor.info(self.toString())
    # else if w > best-wt
    elif msg.best_wt > self.best_wt:
      # execute procedure change-root
      self.change_root()
    # else if w = best-wt = inf
    elif msg.best_wt == self.best_wt and self.best_wt == INF:
      # halt
      self.halt = True
      for edge in self.adjacent_edges:
        if edge.weight == self.fragment_id:
          if edge.dNode < self.id:
            leader = edge.dNode
          else:
            leader = self.id

      self.leader = leader

      for edge in self.adjacent_edges:
        if edge.state == EdgeState.BRANCH:
          mailboxTo = Mailbox.by_name(str(edge.dNode))
          payload = TerminateMessage(source = self.id, leader = self.leader)
          payload_size_in_bytes = sys.getsizeof(payload)
          comm = mailboxTo.put_async(payload, payload_size_in_bytes)
          self.pending_comms.append(comm)
          this_actor.info(f"[{MessageType.TERMINATE.name} to {edge.dNode}] ({self.id} -- Terminate --> {edge.dNode}) : {{{payload.toString()}}}")
          

  # Response to receipt of Accept on edge j 
  def handleAccept(self, msg):
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
    this_actor.info(f"[{MessageType.ACCEPT.name} from {j.dNode}] ({self.id} <-- Accept -- {j.dNode}) : {{}}")
    #this_actor.info(self.toString())
      
    # test-edge <- nil
    self.test_edge = None
    # if w(j) < best-wt
    if j.weight < self.best_wt:
      # best-edge <- j
      self.best_edge = j
      # best-wt <- w(j)
      self.best_wt = j.weight
    # execute procedure report
    self.report()

  # Response to receipt of Reject on edge j
  def handleReject(self, msg):
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
    this_actor.info(f"[{MessageType.REJECT.name} from {j.dNode}] ({self.id} <-- Reject -- {j.dNode}) : {{}}")
    #this_actor.info(self.toString())
      
    # if SE(j) = Basic
    if j.state == EdgeState.BASIC:
      # SE(j) <- Rejected
      j.state = EdgeState.REJECTED
      this_actor.info(f"[REJECTED to {j.dNode}] () : {{}}")
    # execute procedure test
    self.test()

  # Response to receipt of Change-root
  def handleChangeRoot(self, msg):
    this_actor.info(f"[{MessageType.CHANGE_ROOT.name} from {msg.source}] ({self.id} <-- Change Root -- {msg.source}) : {{}}")
    #this_actor.info(self.toString())
      
    # execute procedure change-root
    self.change_root()

  def handleTerminate(self, msg):
    this_actor.info(f"[{MessageType.TERMINATE.name} from {msg.source}] ({self.id} <-- Terminate -- {msg.source}) : {{{msg.toString()}}}")
    j = self.get_edge_by_dNode(msg.source)

    self.leader = msg.leader

    for edge in self.adjacent_edges:
      if edge.dNode != j.dNode and edge.state == EdgeState.BRANCH:
        mailboxTo = Mailbox.by_name(str(edge.dNode))
        payload = TerminateMessage(source = self.id, leader = self.leader)
        payload_size_in_bytes = sys.getsizeof(payload)
        comm = mailboxTo.put_async(payload, payload_size_in_bytes)
        self.pending_comms.append(comm)
        this_actor.info(f"[{MessageType.TERMINATE.name} to {edge.dNode}] ({self.id} -- Terminate --> {edge.dNode}) : {{{payload.toString()}}}")

    self.halt = True

  def __init__(self, id, links):
    # Parse arguments
    self.id = int(id)
    self.get_adjacent_edges(links.split())

    # Create async communication endpoint
    self.mailbox = Mailbox.by_name(str(self.id))
    self.pending_comms = []

    # Start sleeping phase
    self.state = NodeState.SLEEPING

    # Initialize future attributes as None
    self.fragment_id = None
    self.level = None
    self.best_edge = None
    self.best_wt = None
    self.test_edge = None
    self.in_branch = None
    self.find_count = None
    self.halt = None
    self.leader = None

  def toString(self):
    return f"Node: {self.id}, Edges: {self.adjacent_edges}, State: {self.state.name}, Fragment id: {self.fragment_id}, Level: {self.level}, Best edge: {self.best_edge}, Best weight: {self.best_wt}, Test edge: {self.test_edge}, In branch: {self.in_branch}, Find Count: {self.find_count}, Halt: {self.halt}"

  def __call__(self):
    total_compute_size_in_flops = 0 # how many computations did so far while in sleepy state
    max_total_compute_size_in_flops = random.randint(5, 50) # threshold for self-awakening
    self.halt = False
    while not self.halt: # Start asynchronous algorithm
      result_comm, async_data = self.mailbox.get_async() # Initiate the receive operation (does not complete it)
      
      while not result_comm.test(): # Check any message received
        # While asynchronously waiting for messages, do <random_nr> flops computation, then check again
        # Since each node has 1 flops speed, this is the same as sleeping for <random_nr> seconds
        compute_size_in_flops = random.randint(1, 10)
        this_actor.execute(compute_size_in_flops)
        #this_actor.info("waiting")
        ##this_actor.info(self.toString())

        # If node does not get any message for a known period of time, it spontaneously awakes
        if self.state == NodeState.SLEEPING:
          total_compute_size_in_flops += compute_size_in_flops
          # Execute procedure wakeup (cause: self-awakened)
          if total_compute_size_in_flops >= max_total_compute_size_in_flops:
            this_actor.info(f"[SELF-AWAKENED] (Did {total_compute_size_in_flops} flops, more or equal than {max_total_compute_size_in_flops} flop limit!) : {{}}")
            #this_actor.info(self.toString())
            self.wakeup()

      msg = async_data.get()

      if msg.msg_type == MessageType.CONNECT:
        # Execute procedure wakeup (cause: awakened by another node)
        if self.state == NodeState.SLEEPING:
          this_actor.info(f"[AWAKENED by {msg.source}] (Did {total_compute_size_in_flops} flops, less than {max_total_compute_size_in_flops} flop limit!) : {{}}")
          #this_actor.info(self.toString())
          self.wakeup()
        self.handleConnect(msg)

      elif msg.msg_type == MessageType.INITIATE:
        self.handleInitiate(msg)

      elif msg.msg_type == MessageType.TEST:
        # Execute procedure wakeup (cause: awakened by another node)
        if self.state == NodeState.SLEEPING:
          this_actor.info(f"[AWAKENED by {msg.source}] (Did {total_compute_size_in_flops} flops, less than {max_total_compute_size_in_flops} flop limit!) : {{}}")
          #this_actor.info(self.toString())
          self.wakeup()
        self.handleTest(msg)

      elif msg.msg_type == MessageType.REPORT:
        self.handleReport(msg)

      elif msg.msg_type == MessageType.ACCEPT:
        self.handleAccept(msg)

      elif msg.msg_type == MessageType.REJECT:
        self.handleReject(msg)

      elif msg.msg_type == MessageType.CHANGE_ROOT:
        self.handleChangeRoot(msg)

      elif msg.msg_type == MessageType.TERMINATE:
        self.handleTerminate(msg)

    this_actor.info(f"[FINISHED with leader {self.leader}] () : {{}}")
    #this_actor.info(self.toString())
    Comm.wait_all(self.pending_comms)

if __name__ == '__main__':
  assert len(sys.argv) > 2, f"Usage: python AsynchGHS.py 10-nodes-network.xml 10-nodes-network_d.xml"

  e = Engine(sys.argv)

  # Register the classes representing the actors
  e.register_actor("node", Node)

  # Load the platform description and then deploy the application
  e.load_platform(sys.argv[1]) 
  e.load_deployment(sys.argv[2])

  # Run the simulation
  e.run()
  #e.run_until(Engine.clock + 2000)
  this_actor.info("Simulation is over")