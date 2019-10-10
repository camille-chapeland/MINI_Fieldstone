import numpy as np
import sys as sys
import scipy
import math as math
import scipy.stats as stats
import scipy.sparse as sps
from scipy.sparse.linalg.dsolve import linsolve
from scipy.sparse import lil_matrix
import time as timing
import os
import random
import numpy as np
import matplotlib.pyplot as plt

#-----------------------------------SHAPE FUNCTIONS-------------------------------------------

def NNV(r,s):
    NV_0=1-r-s-9*(1-r-s)*r*s 
    NV_1=  r  -9*(1-r-s)*r*s
    NV_2=    s-9*(1-r-s)*r*s
    NV_3=     27*(1-r-s)*r*s
    return NV_0,NV_1,NV_2,NV_3

def dNNVdr(r,s):
    dNdr_0= -1-9*(1-2*r-s)*s 
    dNdr_1=  1-9*(1-2*r-s)*s
    dNdr_2=   -9*(1-2*r-s)*s
    dNdr_3=   27*(1-2*r-s)*s
    return dNdr_0,dNdr_1,dNdr_2,dNdr_3

def dNNVds(r,s):
    dNds_0= -1-9*(1-r-2*s)*r 
    dNds_1=   -9*(1-r-2*s)*r
    dNds_2=  1-9*(1-r-2*s)*r
    dNds_3=   27*(1-r-2*s)*r
    return dNds_0,dNds_1,dNds_2,dNds_3

def NNP(r,s):
    NP_0=1-r-s
    NP_1=r
    NP_2=s
    return NP_0,NP_1,NP_2

#------------------------------------------------------------------------------

def bx(x, y):
    val=((12.-24.*y)*x**4+(-24.+48.*y)*x*x*x +
         (-48.*y+72.*y*y-48.*y*y*y+12.)*x*x +
         (-2.+24.*y-72.*y*y+48.*y*y*y)*x +
         1.-4.*y+12.*y*y-8.*y*y*y)
    return val

def by(x, y):
    val=((8.-48.*y+48.*y*y)*x*x*x+
         (-12.+72.*y-72.*y*y)*x*x+
         (4.-24.*y+48.*y*y-48.*y*y*y+24.*y**4)*x -
         12.*y*y+24.*y*y*y-12.*y**4)
    return val

def velocity_x(x,y):
    val=x*x*(1.-x)**2*(2.*y-6.*y*y+4*y*y*y)
    return val

def velocity_y(x,y):
    val=-y*y*(1.-y)**2*(2.*x-6.*x*x+4*x*x*x)
    return val

def pressure(x,y):
    val=x*(1.-x)-1./6.
    return val

#------------------------------------------------------------------------------

print("-----------------------------")
print("----------fieldstone---------")
print("-----------------------------")

#MINI set-up
ndim=2
mV=4     # number of velocity nodes making up an element
mP=3     # number of pressure nodes making up an element
ndofV=2  # number of velocity degrees of freedom per node
ndofP=1  # number of pressure degrees of freedom 
nqel=7
visu=1
eps=1e-9

#Geometry and Material Variables
Lx=1.     
Ly=1.
nnx=120
nny=120
eta=1.



h=Lx/(nnx-1)
a=h**2

print('mean area given to triangle :', a)

#---------------------------------------
#---------------------------------------
# 6 point integration coeffs and weights 

qcoords_r=np.empty(nqel,dtype=np.float64)  
qcoords_s=np.empty(nqel,dtype=np.float64)  
qweights=np.empty(nqel,dtype=np.float64)  

if nqel==3:
   qcoords_r[0]=1./6.; qcoords_s[0]=1./6.; qweights[0]=1./6.
   qcoords_r[1]=2./3.; qcoords_s[1]=1./6.; qweights[1]=1./6.
   qcoords_r[2]=1./6.; qcoords_s[2]=2./3.; qweights[2]=1./6.

if nqel==6:
   qcoords_r[0]=0.091576213509771 ; qcoords_s[0]=0.091576213509771 ; qweights[0]=0.109951743655322/2.0 
   qcoords_r[1]=0.816847572980459 ; qcoords_s[1]=0.091576213509771 ; qweights[1]=0.109951743655322/2.0 
   qcoords_r[2]=0.091576213509771 ; qcoords_s[2]=0.816847572980459 ; qweights[2]=0.109951743655322/2.0 
   qcoords_r[3]=0.445948490915965 ; qcoords_s[3]=0.445948490915965 ; qweights[3]=0.223381589678011/2.0 
   qcoords_r[4]=0.108103018168070 ; qcoords_s[4]=0.445948490915965 ; qweights[4]=0.223381589678011/2.0 
   qcoords_r[5]=0.445948490915965 ; qcoords_s[5]=0.108103018168070 ; qweights[5]=0.223381589678011/2.0 

if nqel==7:
   qcoords_r[0]=0.1012865073235 ; qcoords_s[0]=0.1012865073235 ; qweights[0]=0.0629695902724 
   qcoords_r[1]=0.7974269853531 ; qcoords_s[1]=0.1012865073235 ; qweights[1]=0.0629695902724 
   qcoords_r[2]=0.1012865073235 ; qcoords_s[2]=0.7974269853531 ; qweights[2]=0.0629695902724 
   qcoords_r[3]=0.4701420641051 ; qcoords_s[3]=0.0597158717898 ; qweights[3]=0.0661970763942 
   qcoords_r[4]=0.4701420641051 ; qcoords_s[4]=0.4701420641051 ; qweights[4]=0.0661970763942 
   qcoords_r[5]=0.0597158717898 ; qcoords_s[5]=0.4701420641051 ; qweights[5]=0.0661970763942 
   qcoords_r[6]=0.3333333333333 ; qcoords_s[6]=0.3333333333333 ; qweights[6]=0.1125000000000 


# generate points on convex hull (square)

N=np.array([[1,0.,0.]])
counter = 1

N=np.append(N, [[counter+1, Lx, Ly]], axis=0)
for i in range(0,nnx):
    counter += 1
    N=np.append(N , [[counter , i*h, 0]] , axis=0)
for i in range(0,nnx):
    counter += 1
    N=np.append(N , [[counter , i*h, Ly]] , axis=0)
for i in range(0,nny):
    counter+=1
    N=np.append(N , [[counter , 0, i*h]] , axis=0)
for i in range(0,nny):
    counter+=1
    N=np.append(N , [[counter , Lx, i*h]] , axis=0)

#produce .node file for triangle

f = open('NodPy.node', 'w')
f.write("%d %d %d %d \n" %(len(N),2,0,0))
for i in range(0,len(N)):
    f.write("%d %5e %5e \n" %(N[i,0],N[i,1],N[i,2]))
f.close()

# call triangle to generate mesh & delaunay triangulation

#myCmd = ('./triangle -j -q30.5 -a0.000402 NodPy.node')
myCmd = ('./triangle -j -q30.5 -a%f NodPy.node' % a)
#myCmd1 = './showme NodPy.1.ele'
os.system(myCmd)
#os.system(myCmd1)
timing.sleep(0.5)
start = timing.time()

# read nb of vertices and triangles from triangle output

f=open('NodPy.1.ele','r')
line = f.readline()
line = line.strip()
line = line.split()
nel = int(line[0])

g=open('NodPy.1.node','r')
line = g.readline()
line = line.strip()
line = line.split()
NP = int(line[0])

NV=NP+nel

print("nel=",nel)
print("NP=",NP)
print("NV=",NV)

iconV = np.zeros((mV,nel),dtype=np.int32) # 3 nodes + bubble

iconV[0,:],iconV[1,:],iconV[2,:]=\
np.loadtxt(f,unpack=True, usecols=[1,2,3],skiprows=0)
iconV[0,:]-=1
iconV[1,:]-=1
iconV[2,:]-=1

#################################################################
# build velocity nodes coordinates and connectivity array 
#################################################################
start = timing.time()

xV=np.zeros(NV,dtype=np.float64)  # x coordinates
yV=np.zeros(NV,dtype=np.float64)  # y coordinates

xV[0:NP],yV[0:NP]=np.loadtxt(g,unpack=True,usecols=[1,2],skiprows=0)

for iel in range (0,nel): #bubble nodes
    xV[NP+iel]=(xV[iconV[0,iel]]+xV[iconV[1,iel]]+xV[iconV[2,iel]])/3.
    yV[NP+iel]=(yV[iconV[0,iel]]+yV[iconV[1,iel]]+yV[iconV[2,iel]])/3.

print("     -> xV (m,M) %.4f %.4f " %(np.min(xV),np.max(xV)))
print("     -> yV (m,M) %.4f %.4f " %(np.min(yV),np.max(yV)))

np.savetxt('gridV.ascii',np.array([xV,yV]).T,header='# x,y,u,v')

for iel in range(0,nel):
    iconV[3,iel]=NP+iel

print("     -> iconV[0,:] (m,M) %.4d %.4d " %(np.min(iconV[0,:]),np.max(iconV[0,:])))
print("     -> iconV[1,:] (m,M) %.4d %.4d " %(np.min(iconV[1,:]),np.max(iconV[1,:])))
print("     -> iconV[2,:] (m,M) %.4d %.4d " %(np.min(iconV[2,:]),np.max(iconV[2,:])))
print("     -> iconV[3,:] (m,M) %.4d %.4d " %(np.min(iconV[3,:]),np.max(iconV[3,:])))

print("grid and connectivity V: %.3f s" % (timing.time() - start))

#################################################################
# build pressure grid (nodes and icon)
#################################################################
start = timing.time()

iconP=np.zeros((3,nel),dtype=np.int32)
xP=np.empty(NP,dtype=np.float64)     # x coordinates
yP=np.empty(NP,dtype=np.float64)     # y coordinates

xP[0:NP]=xV[0:NP]
yP[0:NP]=yV[0:NP]

iconP[0:mP,0:nel]=iconV[0:mP,0:nel]

np.savetxt('gridP.ascii',np.array([xP,yP]).T,header='# x,y')

print("grid and connectivity P: %.3f s" % (timing.time() - start))

#print("     -> iconP[0,:] (m,M) %.4d %.4d " %(np.min(iconV[0,:]),np.max(iconV[0,:])))
#print("     -> iconP[1,:] (m,M) %.4d %.4d " %(np.min(iconV[1,:]),np.max(iconV[1,:])))
#print("     -> iconP[2,:] (m,M) %.4d %.4d " %(np.min(iconV[2,:]),np.max(iconV[2,:])))

#################################################################
# define boundary conditions
#################################################################

NfemV=NV*ndofV       # number of velocity dofs
NfemP=NP             # number of pressure dofs
Nfem=NfemV+NfemP     # total nb of dofs

print ('NfemV=',NfemV)
print ('NfemP=',NfemP)
print ('Nfem =',Nfem)
print("-----------------------------")

start = timing.time()

bc_fix=np.zeros(NfemV,dtype=np.bool)  # boundary condition, yes/no
bc_val=np.zeros(NfemV,dtype=np.float64)  # boundary condition, value

for i in range(0,NV):
    if xV[i]/Lx<eps:
       bc_fix[i*ndofV]   = True ; bc_val[i*ndofV]   = 0.
       bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.
    if xV[i]/Lx>(1-eps):
       bc_fix[i*ndofV]   = True ; bc_val[i*ndofV]   = 0.
       bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.
    if yV[i]/Ly<eps:
       bc_fix[i*ndofV]   = True ; bc_val[i*ndofV]   = 0.
       bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.
    if yV[i]/Ly>(1-eps):
      bc_fix[i*ndofV]   = True ; bc_val[i*ndofV]   = 0.
      bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.

print("boundary conditions: %.3f s" % (timing.time() - start))

#################################################################
# compute area of elements
#################################################################
start = timing.time()

area    = np.zeros(nel,dtype=np.float64) 
dNNNVdr = np.zeros(mV,dtype=np.float64)  # shape functions derivatives
dNNNVds = np.zeros(mV,dtype=np.float64)  # shape functions derivatives

for iel in range(0,nel):
    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        dNNNVdr[0:mV]=dNNVdr(rq,sq)
        dNNNVds[0:mV]=dNNVds(rq,sq)
        jcb=np.zeros((ndim,ndim),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*yV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*yV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        area[iel]+=jcob*weightq

amin = np.min(area)
amax = np.max(area)

print("     -> area (m,M) %.4e %.4e " %(amin,amax))
print("     -> total area %.6f " %(area.sum()))

print("compute elements areas: %.3f s" % (timing.time() - start))

###### Make a area distribution histogram
plt.hist(area,bins='auto', range=(amin,amax))
plt.title('Distribution of area allocated by Triangle mesher')
plt.xlabel('Area')
plt.ylabel('#  of elements')
plt.xlim(amin, amax)

plt.savefig('AreaDist.png')

np.savetxt('area.ascii',area)

#################################################################
#################################################################
start = timing.time()

a_mat = np.zeros((Nfem,Nfem),dtype=np.float64)
K_mat = np.zeros((NfemV,NfemV),dtype=np.float64) # matrix K 
G_mat = np.zeros((NfemV,NfemP),dtype=np.float64) # matrix GT

f_rhs = np.zeros(NfemV,dtype=np.float64)         # right hand side f 
h_rhs = np.zeros(NfemP,dtype=np.float64)         # right hand side h 

b_mat = np.zeros((3,ndofV*mV),dtype=np.float64) # gradient matrix B 
N_mat = np.zeros((3,ndofP*mP),dtype=np.float64) # matrix  
NNNV    = np.zeros(mV,dtype=np.float64)           # shape functions V
NNNP    = np.zeros(mP,dtype=np.float64)           # shape functions P
dNNNVdx  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
dNNNVdy  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
dNNNVdr  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
dNNNVds  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
u     = np.zeros(NV,dtype=np.float64)          # x-component velocity
v     = np.zeros(NV,dtype=np.float64)          # y-component velocity
c_mat = np.array([[2,0,0],[0,2,0],[0,0,1]],dtype=np.float64) 

for iel in range(0,nel):

    # set arrays to 0 every loop
    f_el =np.zeros((mV*ndofV),dtype=np.float64)
    K_el =np.zeros((mV*ndofV,mV*ndofV),dtype=np.float64)
    G_el=np.zeros((mV*ndofV,mP*ndofP),dtype=np.float64)
    h_el=np.zeros((mP*ndofP),dtype=np.float64)

    for kq in range (0,nqel):

        # position & weight of quad. point
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]

        NNNV[0:mV]=NNV(rq,sq)
        dNNNVdr[0:mV]=dNNVdr(rq,sq)
        dNNNVds[0:mV]=dNNVds(rq,sq)
        NNNP[0:mP]=NNP(rq,sq)

        # calculate jacobian matrix
        jcb=np.zeros((ndim,ndim),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*yV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*yV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        jcbi = np.linalg.inv(jcb)

        # compute dNdx & dNdy
        xq=0.0
        yq=0.0
        for k in range(0,mV):
            xq+=NNNV[k]*xV[iconV[k,iel]]
            yq+=NNNV[k]*yV[iconV[k,iel]]
            dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
            dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]

        #print (xq,yq)

        # construct 3x8 b_mat matrix
        for i in range(0,mV):
            b_mat[0:3, 2*i:2*i+2] = [[dNNNVdx[i],0.     ],
                                     [0.        ,dNNNVdy[i]],
                                     [dNNNVdy[i],dNNNVdx[i]]]

        # compute elemental a_mat matrix
        K_el+=b_mat.T.dot(c_mat.dot(b_mat))*eta*weightq*jcob

        # compute elemental rhs vector
        for i in range(0,mV):
            f_el[ndofV*i  ]+=NNNV[i]*jcob*weightq*bx(xq,yq)
            f_el[ndofV*i+1]+=NNNV[i]*jcob*weightq*by(xq,yq)

        for i in range(0,mP):
            N_mat[0,i]=NNNP[i]
            N_mat[1,i]=NNNP[i]
            N_mat[2,i]=0.

        G_el-=b_mat.T.dot(N_mat)*weightq*jcob

    # impose b.c. 
    for k1 in range(0,mV):
        for i1 in range(0,ndofV):
            ikk=ndofV*k1          +i1
            m1 =ndofV*iconV[k1,iel]+i1
            if bc_fix[m1]:
               K_ref=K_el[ikk,ikk] 
               for jkk in range(0,mV*ndofV):
                   f_el[jkk]-=K_el[jkk,ikk]*bc_val[m1]
                   K_el[ikk,jkk]=0
                   K_el[jkk,ikk]=0
               K_el[ikk,ikk]=K_ref
               f_el[ikk]=K_ref*bc_val[m1]
               h_el[:]-=G_el[ikk,:]*bc_val[m1]
               G_el[ikk,:]=0

    # assemble matrix K_mat and right hand side rhs
    for k1 in range(0,mV):
        for i1 in range(0,ndofV):
            ikk=ndofV*k1          +i1
            m1 =ndofV*iconV[k1,iel]+i1
            for k2 in range(0,mV):
                for i2 in range(0,ndofV):
                    jkk=ndofV*k2          +i2
                    m2 =ndofV*iconV[k2,iel]+i2
                    K_mat[m1,m2]+=K_el[ikk,jkk]
            for k2 in range(0,mP):
                jkk=k2
                m2 =iconP[k2,iel]
                G_mat[m1,m2]+=G_el[ikk,jkk]
            f_rhs[m1]+=f_el[ikk]
    for k2 in range(0,mP):
        m2=iconP[k2,iel]
        h_rhs[m2]+=h_el[k2]

print("     -> K_mat (m,M) %.4f %.4f " %(np.min(K_mat),np.max(K_mat)))
print("     -> G_mat (m,M) %.4f %.4f " %(np.min(G_mat),np.max(G_mat)))

print("build FE matrix: %.3f s" % (timing.time() - start))

######################################################################
# assemble K, G, GT, f, h into A and rhs
######################################################################
start = timing.time()

rhs = np.zeros(Nfem,dtype=np.float64)         # right hand side of Ax=b
a_mat[0:NfemV,0:NfemV]=K_mat
a_mat[0:NfemV,NfemV:Nfem]=G_mat
a_mat[NfemV:Nfem,0:NfemV]=G_mat.T
rhs[0:NfemV]=f_rhs
rhs[NfemV:Nfem]=h_rhs

#assign extra pressure b.c. to remove null space
#a_mat[Nfem-1,:]=0
#a_mat[:,Nfem-1]=0
#a_mat[Nfem-1,Nfem-1]=1
#rhs[Nfem-1]=0

print("assemble blocks: %.3f s" % (timing.time() - start))

######################################################################
# solve system
######################################################################
start = timing.time()

sol=sps.linalg.spsolve(sps.csr_matrix(a_mat),rhs)

print("solve time: %.3f s" % (timing.time() - start))

######################################################################
# put solution into separate x,y velocity arrays
######################################################################
start = timing.time()

u,v=np.reshape(sol[0:NfemV],(NV,2)).T
p=sol[NfemV:Nfem]

print("     -> u (m,M) %.4f %.4f " %(np.min(u),np.max(u)))
print("     -> v (m,M) %.4f %.4f " %(np.min(v),np.max(v)))
print("     -> p (m,M) %.4f %.4f " %(np.min(p),np.max(p)))

#np.savetxt('velocity.ascii',np.array([xV,yV,u,v]).T,header='# x,y,u,v')
np.savetxt('p.ascii',np.array([xP,yP,p]).T,header='# x,y,p')

print("split vel into u,v: %.3f s" % (timing.time() - start))

######################################################################
# create pressure q on velocity nodes 
######################################################################

q=np.zeros(NV,dtype=np.float64) 
    
for iel in range(0,nel):
    q[iconV[0,iel]]=p[iconV[0,iel]]
    q[iconV[1,iel]]=p[iconV[1,iel]]
    q[iconV[2,iel]]=p[iconV[2,iel]]
    q[iconV[3,iel]]=(p[iconV[0,iel]]+p[iconV[1,iel]]+p[iconV[2,iel]])/3.

######################################################################
# compute elemental strainrate 
######################################################################
start = timing.time()

xc = np.zeros(nel,dtype=np.float64)  
yc = np.zeros(nel,dtype=np.float64)  
exx = np.zeros(nel,dtype=np.float64)  
eyy = np.zeros(nel,dtype=np.float64)  
exy = np.zeros(nel,dtype=np.float64)  
e   = np.zeros(nel,dtype=np.float64)  

for iel in range(0,nel):
    rq = 0.33333
    sq = 0.33333
    weightq = 0.5 
    NNNV[0:mV]=NNV(rq,sq)
    dNNNVdr[0:mV]=dNNVdr(rq,sq)
    dNNNVds[0:mV]=dNNVds(rq,sq)
    jcb=np.zeros((2,2),dtype=np.float64)
    for k in range(0,mV):
        jcb[0,0]+=dNNNVdr[k]*xV[iconV[k,iel]]
        jcb[0,1]+=dNNNVdr[k]*yV[iconV[k,iel]]
        jcb[1,0]+=dNNNVds[k]*xV[iconV[k,iel]]
        jcb[1,1]+=dNNNVds[k]*yV[iconV[k,iel]]
    jcob=np.linalg.det(jcb)
    jcbi=np.linalg.inv(jcb)
    for k in range(0,mV):
        dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
        dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]
    for k in range(0,mV):
        xc[iel] += NNNV[k]*xV[iconV[k,iel]]
        yc[iel] += NNNV[k]*yV[iconV[k,iel]]
        exx[iel] += dNNNVdx[k]*u[iconV[k,iel]]
        eyy[iel] += dNNNVdy[k]*v[iconV[k,iel]]
        exy[iel] += 0.5*dNNNVdy[k]*u[iconV[k,iel]]+\
                    0.5*dNNNVdx[k]*v[iconV[k,iel]]
    e[iel]=np.sqrt(0.5*(exx[iel]*exx[iel]+eyy[iel]*eyy[iel])+exy[iel]*exy[iel])

print("     -> exx (m,M) %.4f %.4f " %(np.min(exx),np.max(exx)))
print("     -> eyy (m,M) %.4f %.4f " %(np.min(eyy),np.max(eyy)))
print("     -> exy (m,M) %.4f %.4f " %(np.min(exy),np.max(exy)))

#np.savetxt('strainrate.ascii',np.array([xc,yc,exx,eyy,exy]).T,header='# xc,yc,exx,eyy,exy')

print("compute press & sr: %.3f s" % (timing.time() - start))

#####################################################################
# compute vrms and avrg q 
#####################################################################
start = timing.time()

vrms=0.
avrg_q=0.

for iel in range (0,nel):
    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV[0:mV]=NNV(rq,sq)
        dNNNVdr[0:mV]=dNNVdr(rq,sq)
        dNNNVds[0:mV]=dNNVds(rq,sq)
        jcb=np.zeros((2,2),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*yV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*yV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        uq=0.
        vq=0.
        qq=0.
        for k in range(0,mV):
            uq+=NNNV[k]*u[iconV[k,iel]]
            vq+=NNNV[k]*v[iconV[k,iel]]
            qq+=NNNV[k]*q[iconV[k,iel]]
        vrms+=(uq**2+vq**2)*weightq*jcob
        avrg_q+=qq*weightq*jcob
    # end for kq
# end for iel

vrms=np.sqrt(vrms)

print("     -> vrms   = %.6e" %(vrms))
print("     -> avrg_q = %.6e" %(avrg_q))

q-=avrg_q
p-=avrg_q

np.savetxt('q_normalised.ascii',np.array([xV,yV,q]).T,header='# x,y,p')
np.savetxt('p_normalised.ascii',np.array([xP,yP,p]).T,header='# x,y,p')

print("compute vrms, avrg_q: %.3fs" % (timing.time() - start))

#################################################################
# compute error fields for plotting
#################################################################

error_u = np.empty(NV,dtype=np.float64)
error_v = np.empty(NV,dtype=np.float64)
error_p = np.empty(NP,dtype=np.float64)

for i in range(0,NV): 
    error_u[i]=u[i]-velocity_x(xV[i],yV[i])
    error_v[i]=v[i]-velocity_y(xV[i],yV[i])

for i in range(0,NP): 
    error_p[i]=p[i]-pressure(xP[i],yP[i])

#################################################################
# compute L2 errors
#################################################################
start = timing.time()

errv=0.
errp=0.
for iel in range (0,nel):
    for kq in range (0,nqel):
        # position & weight of quad. point
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV[0:mV]=NNV(rq,sq)
        dNNNVdr[0:mV]=dNNVdr(rq,sq)
        dNNNVds[0:mV]=dNNVds(rq,sq)
        NNNP[0:mP]=NNP(rq,sq)
        # calculate jacobian matrix
        jcb=np.zeros((ndim,ndim),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*yV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*yV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        jcbi = np.linalg.inv(jcb)

        # compute dNdx & dNdy
        xq=0.
        yq=0.
        uq=0.
        vq=0.
        pq=0.
        for k in range(0,mV):
            xq+=NNNV[k]*xV[iconV[k,iel]]
            yq+=NNNV[k]*yV[iconV[k,iel]]
            uq+=NNNV[k]*u[iconV[k,iel]]
            vq+=NNNV[k]*v[iconV[k,iel]]
        errv+=((uq-velocity_x(xq,yq))**2+(vq-velocity_y(xq,yq))**2)*weightq*jcob
        # end for k
        xq=0.
        yq=0.
        pq=0.
        for k in range(0,mP):
            xq+=NNNP[k]*xP[iconP[k,iel]]
            yq+=NNNP[k]*yP[iconP[k,iel]]
            pq+=NNNP[k]*p[iconP[k,iel]]
        errp+=(pq-pressure(xq,yq))**2*weightq*jcob
        # end for k
    # end for kq
# end for iel

errv=np.sqrt(errv)
errp=np.sqrt(errp)

print('Resolution approximation:',h)

print("     -> nel= %6d ; errv= %.8f ; errp= %.8f" %(nel,errv,errp))

print("compute errors: %.3f s" % (timing.time() - start))

#####################################################################
# plot of solution
#####################################################################

if visu==1:
    vtufile=open('solution.vtu',"w")
    vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
    vtufile.write("<UnstructuredGrid> \n")
    vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(NP,nel))
    #####
    vtufile.write("<Points> \n")
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e %10e %10e \n" %(xV[i],yV[i],0.))
    vtufile.write("</DataArray>\n")
    vtufile.write("</Points> \n")
    #####
    vtufile.write("<CellData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='area' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (area[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='exx' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (exx[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='eyy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (eyy[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='exy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (exy[iel]))
    vtufile.write("</DataArray>\n")

    vtufile.write("</CellData>\n")
    #####
    vtufile.write("<PointData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='velocity' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e %10e %10e \n" %(u[i],v[i],0.))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='p' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e \n" %p[i])
    vtufile.write("</DataArray>\n")

    #--
    vtufile.write("<DataArray type='Float32' Name='error u' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e \n" %error_u[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='error v' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e \n" %error_v[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='error p' Format='ascii'> \n")
    for i in range(0,NP):
        vtufile.write("%10e \n" %error_p[i])
    vtufile.write("</DataArray>\n")

    #--
    vtufile.write("</PointData>\n")
    #####
    vtufile.write("<Cells>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d %d %d \n" %(iconV[0,iel],iconV[1,iel],iconV[2,iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %((iel+1)*3))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %5)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</Cells>\n")
    #####
    vtufile.write("</Piece>\n")
    vtufile.write("</UnstructuredGrid>\n")
    vtufile.write("</VTKFile>\n")
    vtufile.close()

print("-----------------------------")
print("------------the end----------")
print("-----------------------------")
