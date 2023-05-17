from simgrid import Engine, this_actor, Mailbox, Comm
import random
from enum import Enum
import sys
from dataclasses import dataclass

class MessageType(Enum):
  CONNECT = 0

class NodeState(Enum):
  SLEEPING = 0
  FIND = 1
  FOUND = 2

class EdgeState(Enum):
  BASIC = 0
  BRANCH = 1
  REJECTED = 2

@dataclass
class Message:
  source: int
  msg_type: int
  msg_args: list[str]

@dataclass
class Edge:
  dNode: int
  weight: int
  state: int

  @property
  def toString(self):
    return "(N: " + str(self.dNode) + ", W: " + str(self.weight) + ", T: " + str(self.state) + ")"

class Node:
  def print_adjacent_edges(self):
    msg = ""
    for e in self.adjacent_edges:
      msg += e.toString + " "
    this_actor.info(f"My adjacent edges are: {msg}")

  def get_adjacent_edges(self):
    self.adjacent_edges = []
    for neighbour, distance in enumerate(self.links):
      if int(distance) > 0:
        self.adjacent_edges.append(Edge(dNode = int(neighbour), weight = int(distance), state = EdgeState.BASIC.value))

  def get_edge_by_dNode(self, dNode):
    for edge in self.adjacent_edges:
      if edge.dNode == dNode:
        return edge

  def wakeup(self):
    m = min(self.adjacent_edges, key = lambda x: x.weight)
    this_actor.debug(f"Minimum adjacent edge is: " + m.toString)
    m.state = EdgeState.BRANCH.value
    self.level = 0
    self.state = NodeState.FOUND.value
    self.find_count = 0

    mailboxTo = Mailbox.by_name(str(m.dNode))
    payload = Message(source = self.id, msg_type = MessageType.CONNECT.value, msg_args = [self.level])
    payload_size_in_bytes = 1

    comm = mailboxTo.put_async(payload, payload_size_in_bytes)
    self.pending_comms.append(comm)
    this_actor.info(f"[{MessageType.CONNECT.name}] ({self.id} -> {m.dNode})")

  def onConnect(self, msg):
    this_actor.info(f"[{MessageType.CONNECT.name}] ({self.id} <- {msg.source})")

    source_level = msg.msg_args[0]
    j = self.get_edge_by_dNode(msg.source)
 
    if source_level < self.level:
      this_actor.info("TODO")
    elif j.state == EdgeState.BASIC.value:
      this_actor.info("TODO")
      #j.state = EdgeState.BASIC.value

  def __init__(self, id, links):
    self.id = int(id)
    self.links = links.split()
    self.mailbox = Mailbox.by_name(str(self.id))
    self.get_adjacent_edges()
    self.state = NodeState.SLEEPING.value
    self.pending_comms = []

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
        if self.state == NodeState.SLEEPING.value:
          total_compute_size_in_flops += compute_size_in_flops
          # Execute procedure wakeup (cause: self-awakened)
          if total_compute_size_in_flops >= max_total_compute_size_in_flops:
            this_actor.info(f"[SELF-AWAKENED] (Did {total_compute_size_in_flops} flops, more than {max_total_compute_size_in_flops} flop limit!)")
            self.wakeup()

      msg = async_data.get()

      if msg.msg_type == MessageType.CONNECT.value:
        # Execute procedure wakeup (cause: awakened by another node)
        if self.state == NodeState.SLEEPING.value:
          this_actor.info(f"[AWAKENED by {msg.source}] (Did {total_compute_size_in_flops} flops, less than {max_total_compute_size_in_flops} flop limit!)")
          self.wakeup()
        self.onConnect(msg)

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