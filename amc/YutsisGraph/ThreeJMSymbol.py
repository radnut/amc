
from copy import copy

class ThreeJMSymbol:
    """"3JM-symbol class"""

    def __init__(self,_indices,_signs):
        """Constructor method"""

        # Conversion of Clebsch-Gordan coefficient into 3JM-symbol
        # ( j1 j2 | j3 )                                       ( j1 j2  j3 )
        # ( m1 m2 | m3 ) = (-1)^{ j1 - j2 + m3 } sqrt{2j3 + 1} ( m1 m2 -m3 )

        # J indices
        self.indices = copy(_indices)

        # Signs of M indices
        self.signs = copy(_signs)

        # Phases
        self.indices[0].jphase += 1
        self.indices[1].jphase -= 1
        self.indices[2].mphase += self.signs[2]

        # jhat factor
        self.indices[2].jhat += 1

        # M sign
        self.signs[2] *= -1

        # Negative angular-momentum projection indices in a 3JM-symbol
        # are assumed to be accompanied with a (-1)^{j-m} phase:
        #                          ( j1 j2 j3 )
        #                          ( m1 m2 m3 )
        #                          ( j1 j2 j3 )
        #             (-1)^{j1-m1} (-m1 m2 m3 )
        #                          ( j1 j2 j3 )
        #       (-1)^{j1-m1+j2-m2} (-m1-m2 m3 )
        #                          ( j1 j2 j3 )
        # (-1)^{j1-m1+j2-m2+j3-m3} (-m1-m2-m3 )
        # Add a (-1)^{j-m} phase for each of the negative projection
        # to account for this property ((-1)^{2j-2m} = 1)
        for k in range(3):
            if self.signs[k] == -1:
                self.indices[k].jphase += 1
                self.indices[k].mphase -= 1

        # Flag used in the canonicalization process
        self.alreadyFliped = False

    def getIdx(self,k):
        """Get the corresponding index"""

        return self.indices[k]

    def setIdx(self,_idx,k):
        """Set the corresponding index"""

        self.indices[k] = _idx

    def exchange(self,k1,k2):
        """Exchange two couples (idx,sign) with the corresponding phase factor"""

        # ( j1 j2 j3 )                   ( j1 j3 j2 )
        # ( m1 m2 m3 ) = (-1)^{j1+j2+j3} ( m1 m3 m2 ) = ...

        # Necessary conditions
        if not (k1 in range(3) and k2 in range(3) and k1 != k2):
            return

        # Exchange index
        idx = self.indices[k1]
        self.indices[k1] = self.indices[k2]
        self.indices[k2] = idx

        # Exchange sign
        sign = self.signs[k1]
        self.signs[k1] = self.signs[k2]
        self.signs[k2] = sign

        # Phase factor
        for k in range(3):
            self.indices[k].jphase += 1

    def getSign(self,k):
        """Get the corresponding sign"""

        return self.signs[k]

    def flipSigns(self):
        """Flip the sign of angular momentum projections"""

        if not self.alreadyFliped:
            # Flip the signs
            for k in range(3):
                self.signs[k] *= -1

            # Add phase factor if needed
            #              ( j1 j2 j3 )                                 ( j1 j2 j3 )
            # (-1)^{j1-m1} (-m1 m2 m3 ) = (-1)^{2j1} (-1)^{j2-m2+j3-m3} ( m1-m2-m3 )
            for k,idx in enumerate(self.indices):
                if self.signs[k] == +1:
                    idx.jphase += 2

            # Set the flag to True
            self.alreadyFliped = True

        else:
            print('Error: Try to flip sign of a 3JM-Symbol twice !!!')

    def __str__(self):
        """String"""

        stringTemplate = "3JM-symbol: %8s(%1s) %8s(%1s) %8s(%1s)"

        return stringTemplate%(self.indices[0].jtex, '+' if self.signs[0] == 1 else '-',
                               self.indices[1].jtex, '+' if self.signs[1] == 1 else '-',
                               self.indices[2].jtex, '+' if self.signs[2] == 1 else '-')

