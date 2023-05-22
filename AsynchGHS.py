from simgrid import Engine, this_actor, Mailbox, Comm
import random
from enum import Enum
import sys
from dataclasses import dataclass

class MessageType(Enum):
  CONNECT = 0
  INITIATE = 1

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
  def __init__(self, source: int, level: int, fragmentId: int, state: int):
      super().__init__(source=source, msg_type=MessageType.INITIATE)
      self.level = level
      self.fragmentId = fragmentId
      self.state = state

  def toString(self):
    return f"Level = {self.level}, FragmentId = {self.fragmentId}, State = {self.state}"

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
    return "(N: " + str(self.dNode) + ", W: " + str(self.weight) + ", T: " + str(self.state.value) + ")"

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

  def wakeup(self):
    # Let m be adjacent edge of minimum weight
    m = min(self.adjacent_edges, key = lambda x: x.weight)
    this_actor.debug(f"Minimum adjacent edge is: " + m.toString)

    # SE(m) <- Branch
    m.state = EdgeState.BRANCH

    # LN <- 0
    self.level = 0

    # SN <- Found
    self.state = NodeState.FOUND

    # Find-count <- 0
    self.find_count = 0

    # FN <- 0 (Not in the algorithm)
    self.fragmentId = 0

    # Send Connect(O) on edge m
    mailboxTo = Mailbox.by_name(str(m.dNode))
    payload = ConnectMessage(source = self.id, level = self.level)
    payload_size_in_bytes = sys.getsizeof(payload)
    comm = mailboxTo.put_async(payload, payload_size_in_bytes)
    self.pending_comms.append(comm)
    this_actor.info(f"[{MessageType.CONNECT.name} to {m.dNode}] ({self.id} -- Connect --> {m.dNode}, msg: {{{payload.toString()}}})")

  def handleConnect(self, msg):
    this_actor.info(f"[{MessageType.CONNECT.name} from {msg.source}] ({self.id} <-- Connect -- {msg.source}, msg: {{{msg.toString()}}})")
    # Get edge j
    j = self.get_edge_by_dNode(msg.source)
 
    # If L < LN
    if msg.level < self.level:
      # SE(j) <- Branch
      j.state = EdgeState.BRANCH

      # Send Initiate(LN, FN, SN) on edge j
      mailboxTo = Mailbox.by_name(str(msg.source))
      payload = InitiateMessage(source = self.id, level = self.level, fragmentId = self.fragmentId, state = self.state)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.INITIATE.name} to {msg.source}] ({self.id} -- Initiate --> {msg.source}, msg: {{{payload.toString()}}})")

    # Else if SE(j) = Basic
    elif j.state == EdgeState.BASIC:
      # Place received message on end of queue
      self.incoming_messages.append(msg)

    else:
      # Send Initiate(LN + 1, w(j), Find) on edge j
      mailboxTo = Mailbox.by_name(str(msg.source))
      payload = InitiateMessage(source = self.id, level = self.level + 1, fragmentId = j.weight, state = NodeState.FIND)
      payload_size_in_bytes = sys.getsizeof(payload)
      comm = mailboxTo.put_async(payload, payload_size_in_bytes)
      self.pending_comms.append(comm)
      this_actor.info(f"[{MessageType.INITIATE.name} to {msg.source}] ({self.id} -- Initiate --> {msg.source}, msg: {{{payload.toString()}}})")

  def handleInitiate(self, msg):
      this_actor.info(f"[{MessageType.INITIATE.name} from {msg.source}] ({self.id} <-- Initiate -- {msg.source}, msg: {{{msg.toString()}}})")

  def __init__(self, id, links):
    # Parse arguments
    self.id = int(id)
    self.get_adjacent_edges(links.split())

    # Create async communication endpoint
    self.mailbox = Mailbox.by_name(str(self.id))
    self.pending_comms = []

    # Initialize FIFO incoming messages queue
    self.incoming_messages = []

    # Start sleeping phase
    self.state = NodeState.SLEEPING

  def __call__(self):
    total_compute_size_in_flops = 0 # how many computations did so far while in sleepy state
    max_total_compute_size_in_flops = random.randint(5, 50) # threshold for self-awakening
    done = False
    while not done: # Start asynchronous algorithm
      result_comm, async_data = self.mailbox.get_async() # Initiate the receive operation (does not complete it)
      
      while not result_comm.test(): # Check any message received
        # While asynchronously waiting for messages, do <random_nr> flops computation, then check again
        # Since each node has 1 flops speed, this is the same as sleeping for <random_nr> seconds
        compute_size_in_flops = random.randint(1, 10)
        this_actor.execute(compute_size_in_flops)

        # If node does not get any message for a known period of time, it spontaneously awakes
        if self.state == NodeState.SLEEPING:
          total_compute_size_in_flops += compute_size_in_flops
          # Execute procedure wakeup (cause: self-awakened)
          if total_compute_size_in_flops >= max_total_compute_size_in_flops:
            this_actor.info(f"[SELF-AWAKENED] (Did {total_compute_size_in_flops} flops, more or equal than {max_total_compute_size_in_flops} flop limit!)")
            self.wakeup()

      msg = async_data.get()

      if msg.msg_type == MessageType.CONNECT:
        # Execute procedure wakeup (cause: awakened by another node)
        if self.state == NodeState.SLEEPING:
          this_actor.info(f"[AWAKENED by {msg.source}] (Did {total_compute_size_in_flops} flops, less than {max_total_compute_size_in_flops} flop limit!)")
          self.wakeup()
        self.handleConnect(msg)

      elif msg.msg_type == MessageType.INITIATE:
        self.handleInitiate(msg)

    #Comm.wait_all(self.pending_comms)

if __name__ == '__main__':
  assert len(sys.argv) > 2, f"Usage: python AsynchGHS.py 10-nodes-network.xml 10-nodes-network_d.xml"

  e = Engine(sys.argv)

  # Register the classes representing the actors
  e.register_actor("node", Node)

  # Load the platform description and then deploy the application
  e.load_platform(sys.argv[1]) 
  e.load_deployment(sys.argv[2])

  # Run the simulation
  e.run_until(Engine.clock + 200)

  this_actor.info("Simulation is over")