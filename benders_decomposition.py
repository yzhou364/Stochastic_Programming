import gurobipy as gp
from gurobipy import *
import numpy as np
import data as data

# Set the sets and arcs
Fset = data.Fset  # set of facilities (list of strings)
Hset = data.Hset  # set of warehouses (list of strings)
Cset = data.Cset  # set of customers (list of strings)
Sset = data.Sset  # set of scenarios (list of strings)
arcExpCost = data.arcExpCost  # arc expansion costs (dictionary mapping F,H and H,C pairs to floats)
facCap = data.facCap   # facility capacities (dictionary mapping F to floats) 
curArcCap = data.curArcCap  # current arc capacities (dictionary mapping (i,j) to floats, where either 
                                 # i is facility, j is warehouse, or i is warehouse and j is customer
unmetCost = data.unmetCost  # penalty for unment customer demands (dicationary mapping C to floats)
demScens = data.demScens  # demand scenarios (dictionary mapping (i,k) tuples to floats, where i is customer, k is
                                #scenario


### Define sets of arcs (used as keys to dictionaries)
FHArcs = [(i,j) for i in Fset for j in Hset]  ## arcs from facilities to warehouses
HCArcs = [(i,j) for i in Hset for j in Cset]   ## arcs from warehouses to customers
AllArcs = FHArcs + HCArcs


start = time.time()
master = Model('Master_Problem')

capAdd = {}
