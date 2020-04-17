from gurobipy import *
import time
import numpy as np
import matplotlib.pyplot as plt

import data as data

# Set the sets and arcs
Fset = data.Fset
Hset = data.Hset
Cset = data.Cset
Sset = data.Sset
arcExpCost = data.arcExpCost
facCap = data.facCap
curArcCap = data.curArcCap
unmetCost = data.unmetCost
demScens = data.demScens

FHArcs = [(i,j) for i in Fset for j in Hset]
HCArcs = [(i,j) for i in Hset for j in Cset]
AllArcs = FHArcs +HCArcs

# Bulding the model
unmetCostScens = [unmetCost[i]/float(len(Sset)) for i in Cset for k in Sset]

start = time.time()
m = Model("netdesign")

capAdd = m.addVars(AllArcs, obj = arcExpCost, name = "CapExp")

flow = m.addVars(AllArcs, Sset, name = "Flow")

unmet = {}
unmet = m.addVars(Cset, Sset, obj = unmetCostScens, name = "Unmet" )

m.modelSense = GRB.MINIMIZE

m.update()

m.addConstrs((flow[i,j,k] <= curArcCap[i,j] + capAdd[i,j] for (i,j) in AllArcs for k in Sset), name = "Capacity")

m.addConstrs((flow.sum(i,"*",k) <= facCap[i]  for i in Fset for k in Sset), name = "FacCap")

m.addConstrs((flow.sum(i,"*",k) == flow.sum("*",i,k) for i in Hset for k in Sset), name = "WhBal")

m.addConstrs((flow.sum("*",i,k) + unmet[i,k] >= demScens[i,k] for i in Cset for k in Sset),name = "CustDem")

m.update()

m.optimize()

stochobjval = m.objVal
print('\nEXPECTED COST: %g' % m.objVal)
print('\nExpansion Cost : %g' % (sum(capAdd[i,j].x*arcExpCost[i,j] for i,j in AllArcs)))
print('SOLUTION:')
for (i,j) in AllArcs:
    if capAdd[i,j].x > 0.00001:
        print('Arc %s,%s expanded by %g' % (i,j,capAdd[i,j].x))
print('AVERAGE UNMET DEMAND:')
for i in Cset:
    avgunmet = sum(unmet[i,k].x for k in Sset)/(len(Sset))
    print(' Customer %s: %g' % (i, avgunmet))
    
print('Total time for building and solving extensive form = ', time.time() - start)

mvm = Model("mvnetdesign")

mvcapAdd = mvm.addVars(AllArcs, obj = arcExpCost, name = "CapExp" )

mvflow = mvm.addVars(AllArcs, name = 'Flow')

mvunmet = mvm.addVars(Cset, obj = unmetCost, name = 'Unmet')

mvm.modelSense = GRB.MINIMIZE
mvm.update()

mvm.addConstrs((mvflow[i,j] <= curArcCap[i,j] + mvcapAdd[i,j] for (i,j) in AllArcs), name='Capacity')

mvm.addConstrs((mvflow.sum(i,'*') <= facCap[i] for i in Fset), name='FacCap')

mvm.addConstrs((mvflow.sum(i,'*') - mvflow.sum('*',i) == 0 for i in Hset), name='WhBal')

mvm.addConstrs((mvflow.sum('*',i) + mvunmet[i] >= sum(demScens[i,k] for k in Sset)/float(len(Sset)) for i in Cset), name='CustDem')

mvm.update()
mvm.optimize()

print('\MEAN VALUE PROBLEM COST: %g' % mvm.objVal)
print('SOLUTION:')
for (i,j) in AllArcs:
    if mvcapAdd[i,j].x > 0.00001:
        print('Arc %s,%s expanded by %g' % (i,j,mvcapAdd[i,j].x))
 
# Solve sp with mvm value       
for (i,j) in AllArcs:
    capAdd[i,j].lb = capAdd[i,j].ub = mvcapAdd[i,j].x
    
m.update()
m.optimize()

print('\nEXPECTED COST OF MEAN VALUE SOLUTION: %g' % m.objVal)
print('\nExpansion Cost mean value solution: %g' % (sum(capAdd[i,j].x*arcExpCost[i,j] for i,j in AllArcs)))
print('\nVALUE OF STOCHASTIC SOLUTION: %g' % (m.objVal - stochobjval))

