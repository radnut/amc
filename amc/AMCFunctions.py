from __future__ import (division, absolute_import, print_function)

from copy import copy
from itertools import permutations
from sympy.combinatorics.permutations import Permutation


def deltaReduction(Y, jschAmplitudes):
    """Change indices in amplitudes according to the delta list
    /!\ Remove also external deltas !!!"""

    # Copy the list of deltas
    deltas = copy(Y.deltas)

    # Loop over the deltas
    for delta in deltas:

        # If delta already considered then continue
        if delta not in Y.deltas:
            continue

        # Initialize deltaList with delta
        deltaList = [delta]

        # Loop over the deltaList
        for deltap in deltaList:

            # Get indices
            idx1 = deltap.indices[0]
            idx2 = deltap.indices[1]

            # Find other delta that should be in deltaList
            for deltapp in deltas:

                # If already added then continue
                if deltapp in deltaList:
                    continue

                # If deltas share an index then add deltapp
                if idx1 in deltapp.indices or idx2 in deltapp.indices:
                    deltaList.append(deltapp)

        # Sort the list of deltas
        deltaList.sort(key=lambda dlt: ((0 if dlt.indices[0].zero else 1), (0 if dlt.indices[0].external else 1), (0 if dlt.indices[0].is_particle else 1), len(dlt.indices[0].name), dlt.indices[0].name))

        # Get surviving index
        survivingIdx = deltaList[0].indices[0]

        # Apply delta to indices
        # 1) The ones not containing survivingIdx
        # 2) The ones containing survivingIdx
        for dlt in [delta for delta in deltaList if survivingIdx not in delta.indices]:
            dlt.apply()
        for dlt in [delta for delta in deltaList if survivingIdx in delta.indices]:
            dlt.apply()

        # Get list of all other indices
        idxList = []
        for dlt in deltaList:
            for idx in dlt.indices:
                if idx != survivingIdx and idx not in idxList:
                    idx.constrained_to = survivingIdx
                    idxList.append(idx)

        # Apply indices change
        for idx in idxList:
            for amp in jschAmplitudes:
                if idx == amp.diagonalIdx:
                    amp.diagonalIdx = survivingIdx
                for kidxp, idxp in enumerate(amp.interIndices):
                    if idx == idxp:
                        amp.interIndices[kidxp] = survivingIdx

        # Remove deltas from Yutsis
        for deltap in deltaList:
            Y.deltas.remove(deltap)


def partition(N, depth=0):
    """ Recursive function that return a list of
    all possible permutations of len(N) lists of N[i] objects"""

    # If last level achieved
    if len(N) == depth:
        return [[]]

    # List of permutation of a given depth
    myList = []

    # Go the next level
    for k in partition(N, depth=depth + 1):

        # Loop over the permutations of the list range(N[depth])
        for perm in permutations(range(N[depth]), N[depth]):

            # Copy the prexising k permutation
            myList.append(copy(k))

            # Add the next level of permutation to it
            myList[-1].append(perm)

    return myList


def applyPermutation(newAmplitudes, permutation):
    """ Apply the permutation to all amplitudes"""

    # Initialize signature
    signature = 1

    # For all permutations
    for k, perm in enumerate(permutation):
        # Get the amplitude corresponding to perm
        # k//2 (amp contain both left and right indices)
        amp = newAmplitudes[k // 2]

        # Apply perm to amp
        signature *= permute(k, amp, perm)

    return signature


def permute(k, amp, perm):
    """ Apply the permutation to the amplitude """

    # If left indices
    if k % 2 == 0:
        # Already placed indices have been put to the leftest part of the left indices
        shift = len(amp.indices[:amp.I]) - len(perm)
        indices = amp.indices[shift:amp.I]

    # Else right indices
    else:
        # Already placed indices have been put to the leftest part of the right indices
        shift = len(amp.indices[amp.I:]) - len(perm)
        if amp.I > (amp.I + amp.J) // 2:
            indices = amp.indices[amp.I + shift:]
        else:
            if shift <= (amp.I + amp.J) // 2:
                indices = amp.indices[amp.I:(amp.I + amp.J) // 2] + amp.indices[(amp.I + amp.J) // 2 + shift:]
            else:
                indices = amp.indices[amp.I:(amp.I + amp.J) // 2 - (shift - (amp.I + amp.J) // 2)]

    # Apply the permutation
    indices = [x[1] for x in sorted(enumerate(indices), key=lambda x: [l for l, p in enumerate(perm) if p == x[0]][0])]

    # Set sorted indices
    if k % 2 == 0:
        amp.indices[shift:amp.I] = indices
    else:
        if amp.I > (amp.I + amp.J) // 2:
            amp.indices[amp.I + shift:] = indices
        else:
            if shift <= (amp.I + amp.J) // 2:
                amp.indices[amp.I:(amp.I + amp.J) // 2] = indices[:(amp.I + amp.J) // 2 - amp.I]
                amp.indices[(amp.I + amp.J) // 2 + shift:] = indices[(amp.I + amp.J) // 2 - amp.I:]
            else:
                amp.indices[amp.I:(amp.I + amp.J) // 2 - (shift - (amp.I + amp.J) // 2)] = indices

    # Return the signature of the permutation
    return Permutation(perm).signature()


def smartPermutations(prelimPerm, alreadyPlaced, extIndices, keqnI, amplitudes):
    """Preprocess permutations by placing equivalent indices in the firsts CG coefficients"""

    # Add Left and Right indices of the LHS tensor
    allIndices = [extIndices[:keqnI], extIndices[keqnI:]]

    # Loop over RHS tensors
    for amp in amplitudes:

        # Amplitude I, J and indices
        ampI = amp[1]
        ampJ = amp[2]
        ampIndices = amp[4]

        # Add Left and Right indices of the tensor
        allIndices.append(ampIndices[:ampI])
        allIndices.append(ampIndices[ampI:])

    prelimPerm.extend(list(range(len(amp))) for amp in allIndices[2:])
    alreadyPlaced.extend(0 for amp in allIndices[2:])
    for kamp1, amp1 in enumerate(allIndices):

        # If already treated once then no other treatment
        if kamp1 - 2 >= 0 and alreadyPlaced[kamp1 - 2] != 0:
            continue

        # I,J
        ampI1, ampJ1 = len(allIndices[kamp1 - kamp1 % 2]), len(allIndices[kamp1 - kamp1 % 2 + 1])

        for kamp2, amp2 in enumerate(allIndices):

            # Consider all couples only one time
            if kamp2 < kamp1 + 1 + (kamp1 + 1) % 2:
                continue

            # If already treated once then no other treatment
            if kamp1 - 2 >= 0 and alreadyPlaced[kamp1 - 2] != 0:
                break

            # If already treated once then no other treatment
            if kamp2 - 2 >= 0 and alreadyPlaced[kamp2 - 2] != 0:
                continue

            # I,J
            ampI2, ampJ2 = len(allIndices[kamp2 - kamp2 % 2]), len(allIndices[kamp2 - kamp2 % 2 + 1])

            # Get list of common indices
            common = []
            for idx1 in amp1:
                for idx2 in amp2:
                    if idx1 == idx2:
                        common.append(idx1)

            # Amplitude 0 (kamp1 = 0 left part, kamp1 = 1 right part)
            # Can not be permuted so dictates the permutation of the other amplitude
            if kamp1 == 0:

                # # Two-body external
                # #40 k1 k2 | k3 k4 0 1 2 3
                # #31 k1 k2 | k3    0 1
                # #22 k1 k2 |       0 1
                # #13 k1    |        no
                # #04       |        no
                # if ampI1+ampJ1 == 4:
                #    if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                #        common = amp1[0:2]
                #    elif ampI1 >= 4 and amp1[2] in common and amp1[3] in common:
                #        common = amp1[2:4]
                #    else:
                #        common = []

                # # Three-body external
                # #60 k1 k2 k3 | k4 k5 k6 0 1 3 4
                # #51 k1 k2 k3 | k4 k5    0 1 3 4
                # #42 k1 k2 k3 | k4       0 1
                # #33 k1 k2 k3 |          0 1
                # #24 k1 k2    |          0 1
                # #15 k1       |           no
                # #06          |           no
                # if ampI1+ampJ1 == 6:
                #    if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                #        common = amp1[0:2]
                #    elif ampI1 >= 5 and amp1[3] in common and amp1[4] in common:
                #        common = amp1[3:5]
                #    else:
                #        common = []

                # A-body external
                if ampI1 + ampJ1 >= 4:
                    if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                        common = amp1[0:2]
                    elif ampI1 >= (ampI1 + ampJ1) // 2 + 2 and amp1[(ampI1 + ampJ1) // 2] in common and amp1[(ampI1 + ampJ1) // 2 + 1] in common:
                        common = amp1[(ampI1 + ampJ1) // 2:(ampI1 + ampJ1) // 2 + 2]
                    else:
                        common = []

            elif kamp1 == 1:

                # # Two-body external
                # #40       |        no
                # #31       |    k1  no
                # #22       | k1 k2 0 1
                # #13    k1 | k2 k3 1 2
                # #04 k1 k2 | k3 k4 2 3 0 1
                # if ampI1+ampJ1 == 4:
                #    if ampJ1 >= 2 and amp1[ampJ1-2] in common and amp1[ampJ1-2+1] in common:
                #        common = amp1[ampJ1-2:ampJ1]
                #    elif ampJ1 >= 4 and amp1[ampJ1-4] in common and amp1[ampJ1-4+1] in common:
                #        common = amp1[ampJ1-4:ampJ1-2]
                #    else:
                #        common = []

                # # Three-body external
                # #60          |           no
                # #51          |       k1  no
                # #42          |    k1 k2  no
                # #33          | k1 k2 k3 0 1
                # #24       k1 | k2 k3 k4 1 2
                # #15    k1 k2 | k3 k4 k5 2 3
                # #06 k1 k2 k3 | k4 k5 k6 3 4 0 1
                # if ampI1+ampJ1 == 6:
                #    if ampJ1 >= 3 and amp1[ampJ1-3] in common and amp1[ampJ1-3+1] in common:
                #        common = amp1[ampJ1-3:ampJ1-1]
                #    elif ampJ1 >= 6 and amp1[ampJ1-6] in common and amp1[ampJ1-6+1] in common:
                #        common = amp1[ampJ1-6:ampJ1-4]
                #    else:
                #        common = []

                # A-body external
                if ampI1 + ampJ1 >= 4:
                    if ampJ1 >= (ampI1 + ampJ1) // 2 and amp1[ampJ1 - (ampI1 + ampJ1) // 2] in common and amp1[ampJ1 - (ampI1 + ampJ1) // 2 + 1] in common:
                        common = amp1[ampJ1 - (ampI1 + ampJ1) // 2:ampJ1 - (ampI1 + ampJ1) // 2 + 2]
                    elif ampJ1 >= (ampI1 + ampJ1) and amp1[ampJ1 - (ampI1 + ampJ1)] in common and amp1[ampJ1 - (ampI1 + ampJ1) + 1] in common:
                        common = amp1[ampJ1 - (ampI1 + ampJ1):ampJ1 - (ampI1 + ampJ1) + 2]
                    else:
                        common = []

            # If at least two common indices
            if len(common) >= 2:

                # Get position of common indices
                perm1 = []
                perm2 = []
                for k in range(2):
                    for k1, idx1 in enumerate(amp1):
                        if idx1 == common[k]:
                            perm1.append(k1)
                            break
                    for k2, idx2 in enumerate(amp2):
                        if idx2 == common[k]:
                            perm2.append(k2)
                            break

                # If LHS for amp1
                if kamp1 % 2 == 0:
                    # Indices fixed to the left and other to the right
                    perm1.extend([k for k in range(ampI1) if k not in perm1])

                # Else RHS for amp1
                else:
                    if ampI1 >= (ampI1 + ampJ1) // 2:
                        # Indices fixed to the left and other to the right
                        perm1.extend([k for k in range(ampJ1) if k not in perm1])
                    else:
                        # Indices fixed after rank//2
                        temp = [k for k in range(ampJ1) if k not in perm1]
                        temp2 = temp[:(ampI1 + ampJ1) // 2 - ampI1]
                        temp2.extend(perm1)
                        temp2.extend(temp[(ampI1 + ampJ1) // 2 - ampI1:])
                        perm1 = temp2

                # If LHS for amp2
                if kamp2 % 2 == 0:
                    # Indices fixed to the left and other to the right
                    perm2.extend([k for k in range(ampI2) if k not in perm2])

                # Else RHS for amp2
                else:
                    if ampI2 >= (ampI2 + ampJ2) // 2:
                        # Indices fixed to the left and other to the right
                        perm2.extend([k for k in range(ampJ2) if k not in perm2])
                    else:
                        # Indices fixed after rank//2
                        temp = [k for k in range(ampJ2) if k not in perm2]
                        temp2 = temp[:(ampI2 + ampJ2) // 2 - ampI2]
                        temp2.extend(perm2)
                        temp2.extend(temp[(ampI2 + ampJ2) // 2 - ampI2:])
                        perm2 = temp2

                # If not the LHS amplitude then save the permutation
                if kamp1 - 2 >= 0:
                    prelimPerm[kamp1 - 2] = perm1
                    alreadyPlaced[kamp1 - 2] += 2
                if kamp2 - 2 >= 0:
                    prelimPerm[kamp2 - 2] = perm2
                    alreadyPlaced[kamp2 - 2] += 2

