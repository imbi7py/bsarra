import matplotlib.pyplot as plt
from numpy import ones, exp

ECA = [4.2, 3.5, 3.2, 3, 3.4, 2.1, 1.9, 1.8, 1.9, 2.2, 2.5, 2.8, 2.4, 3.1, 3.3, 2.9, 4.1, 3.9]
Kc = [0.3, 0.5, 0.7, 0.9, 1.1, 0.6, 0.3, 0.5, 0.7, 0.9, 1.1, 0.6, 0.3, 0.5, 0.7, 0.9, 1.1, 0.6]
Kp = [0.75, 0.85, 0.85, 0.75, 0.7, 0.75, 0.75, 0.75, 0.75, 0.7, 0.7, 0.7, 0.7, 0.75, 0.75, 0.7, 0.75, 0.7]
P = [28, 0, 0, 0, 13, 0, 0, 5, 0, 0, 12, 0, 5, 2, 1, 0, 0, 0]
i=0
ETC = ones(len(ECA))
CAD = 100
ARM = CAD*ones(len(ECA))
while i<len(ECA):
    ETC[i] = 15*ECA[i]*Kc[i]*Kp[i]
    if P[i]<ETC[i]:
        ARM[i] = CAD*exp((P[i]-ETC[i])/CAD)
    i=i+1
print(ETC)

#plt.plot(P)
#plt.plot(ETC)
plt.plot(ARM)
plt.show()