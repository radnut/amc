
from copy import copy
from itertools import permutations
from sympy.combinatorics.permutations import Permutation

def deltaReduction(Y,jschAmplitudes):
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
        for dlt in deltaList:
            dlt.sortAccordingToTex()
        deltaList.sort(key = lambda dlt: ((0 if dlt.indices[0].zero else 1),(0 if dlt.indices[0].external else 1),(0 if dlt.indices[0].partIdx else 1),len(dlt.indices[0].jtex),dlt.indices[0].jtex))

        # Get surviving index
        survivingIdx = deltaList[0].indices[0]

        # Get list of all other indices
        idxList = []
        for dlt in deltaList:
            for idx in dlt.indices:
                if idx != survivingIdx and idx not in idxList:
                    idx.hasbeendelta = survivingIdx
                    idxList.append(idx)

        # Apply indices change
        for idx in idxList:
            for amp in jschAmplitudes:
                if idx == amp.diagonalIdx:
                    amp.diagonalIdx = survivingIdx
                for kidxp,idxp in enumerate(amp.interIndices):
                    if idx == idxp:
                        amp.interIndices[kidxp] = survivingIdx

        # Remove deltas from Yutsis
        for deltap in deltaList:
            Y.deltas.remove(deltap)

def partition(N,depth=0):
    """ Recursive function that return a list of
    all possible permutations of len(N) lists of N[i] objects"""

    # If last level achieved
    if len(N) == depth:
        return [[]]

    # List of permutation of a given depth
    myList = []

    # Go the next level
    for k in partition(N,depth=depth+1):

        # Loop over the permutations of the list range(N[depth])
        for perm in permutations(range(N[depth]),N[depth]):

            # Copy the prexising k permutation
            myList.append(copy(k))

            # Add the next level of permutation to it
            myList[-1].append(perm)

    return myList

def applyPermutation(newAmplitudes,permutation):
    """ Apply the permutation to all amplitudes"""

    # Initialize signature
    signature = 1

    # For all permutations
    for k,perm in enumerate(permutation):
        # Get the amplitude corresponding to perm
        # k//2 (amp contain both left and right indices)
        amp = newAmplitudes[k//2]

        # Apply perm to amp
        signature *= permute(k,amp,perm)

    return signature

def permute(k,amp,perm):
    """ Apply the permutation to the amplitude """

    # If left indices
    if k%2 == 0:
        # Already placed indices have been put to the leftest part of the left indices
        shift = len(amp.indices[:amp.I])-len(perm)
        indices = amp.indices[shift:amp.I]

    # Else right indices
    else:
        # Already placed indices have been put to the leftest part of the right indices
        shift = len(amp.indices[amp.I:])-len(perm)
        if amp.I > (amp.I+amp.J)//2:
            indices = amp.indices[amp.I+shift:]
        else:
            if shift <= (amp.I+amp.J)//2:
                indices = amp.indices[amp.I:(amp.I+amp.J)//2] + amp.indices[(amp.I+amp.J)//2+shift:]
            else:
                indices = amp.indices[amp.I:(amp.I+amp.J)//2-(shift-(amp.I+amp.J)//2)]

    # Apply the permutation
    indices = [x[1] for x in sorted(enumerate(indices), key=lambda x: [l for l,p in enumerate(perm) if p==x[0]][0])]

    # Set sorted indices
    if k%2 == 0:
        amp.indices[shift:amp.I] = indices
    else:
        if amp.I > (amp.I+amp.J)//2:
            amp.indices[amp.I+shift:] = indices
        else:
            if shift <= (amp.I+amp.J)//2:
                amp.indices[amp.I:(amp.I+amp.J)//2] = indices[:(amp.I+amp.J)//2-amp.I]
                amp.indices[(amp.I+amp.J)//2+shift:] = indices[(amp.I+amp.J)//2-amp.I:]
            else:
                amp.indices[amp.I:(amp.I+amp.J)//2-(shift-(amp.I+amp.J)//2)] = indices

    # Return the signature of the permutation
    return Permutation(perm).signature()

