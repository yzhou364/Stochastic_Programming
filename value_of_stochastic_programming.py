import numpy as np
import matplotlib.pyplot as plt
from gurobipy import *
import os
import time

import data as data
### Read data
Fset = data.Fset #Factory
Hset = data.Hset #Warehouse
Cset = data.Cset
Sset = data.Sset
arcExpCost = data.arcExpCost
facCap = data.facCap
curArcCap = data.curArcCap
unmetCost = data.unmetCost
demScens = data.demScens

### Build arcs between F,H,C
FHArcs = [(i,j) for i in Fset for j in Hset]
HCArcs = [(i,j) for i in Hset for j in Cset]
AllArcs = FHArcs + HCArcs

alpha = 0.1

### Build models
start = time.time()
m = Model("netdesign")

capAdd = m.addVars(AllArcs, name = "capExp")
flow = m.addVars(AllArcs,Sset, name = "flow")
unmet = m.addVars(Cset,Sset, name = "unmet")
scencost = m.addVars(Sset, name = "scost")
exceed = m.addVars(Sset,name = "exceed")
gamma = m.addVar(lb=-GRB.INFINITY, name = "Gamma")


m.modelSense = GRB.MINIMIZE
m.update()

m.addConstrs(
	(flow[i,j,k] <= curArcCap[i,j] + capAdd[i,j] for (i,j) in AllArcs for k in Sset), name='capacity')
m.addConstrs(
    (flow.sum(i,"*",k) <= facCap[i] for i in Fset for k in Sset), name = "facCap")
m.addConstrs(
    (flow.sum("*",i,k) + unmet[i,k] >= demScens[i,k] for i in Cset for k in Sset), name = "cusDem")
m.addConstrs(
    (flow.sum("*",j,k) == flow.sum(j,"*",k) for j in Hset for k in Sset), name = "whBal")
m.addConstrs(
    (scencost[k] == capAdd.prod(arcExpCost) + quicksum(unmet[i,k]*unmetCost[i] for i in Cset) for k in Sset), name='ScenCostDef')
m.addConstrs(
    (exceed[k] >= scencost[k] - gamma for k in Sset), name = "exceedDef")


### Solve models
allCosts = []
for lam in [0,1,100]:
    m.setObjective(1.0/float(len(Sset))*sum(scencost[k] for k in Sset)+lam*gamma+lam/float(len(Sset))/(1.0-alpha)*sum(exceed[k] for k in Sset))
    
    m.update()
    m.reset()
    
    m.optimize()
    print('\nAVaR of COST : %g' % (gamma.x + sum(exceed[k].x for k in Sset)/float(len(Sset))/(1.0-alpha)))
    print('SOLUTION:')
    for (i,j) in AllArcs:
   		if capAdd[i,j].x > 0.00001:
   			print('Arc %s,%s expanded by %g' % (i,j,capAdd[i,j].x))
    print('\nAverage cost: %g' % (sum(scencost[k].x for k in Sset)/float(len(Sset))))
    print('AVERAGE UNMET DEMAND:') 
    for i in Cset:
   		avgunmet = sum(unmet[i,k].x for k in Sset)/(len(Sset))
   		print('   Customer %s: %g' % (i, avgunmet))
   
    costs = np.zeros(len(Sset))
    kind = 0
    for k in Sset:
   		costs[kind] = scencost[k].x
   		kind = kind+1
    allCosts.append(costs)
   
    print ('total time for building and solving = ', time.time() - start)


plt.hist(allCosts, range=(0,18000),  bins=18)
plt.title('Histogram of Solution Costs')
plt.xlabel('Cost')
plt.ylabel('Frequency')
plt.legend(['Expected value solution', 'AVaR: lambda=1','AVaR: lambda=100'])
plt.show()


