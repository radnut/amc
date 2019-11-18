#!/usr/bin/env python3

from copy import copy
from sympy import Rational
from sys import stdout
from amc.AMCFunctions import deltaReduction,partition,applyPermutation,smartPermutations
from amc.AMCLatexFile import AMCLatexFile
from amc.JTensor import JTensor
from amc.MTensor import MTensor
from amc.YutsisGraph import Idx,YutsisReduction,ClebschGordan

def AMCReduction(equations, outputFileName, doPermutations=False, doSmartPermutations=False, verbose=False, print_threej=False, factorize_ninej=False, keqnMaster=None, ktermMaster=None, kpermMaster=None):
    # Print Latex - Preamble
    TEX = AMCLatexFile(outputFileName)

    selectEqn = keqnMaster is not None
    selectTerm = ktermMaster is not None
    selectPerm = kpermMaster is not None

    # Loop over the equations
    fatalErrorNumb = 0
    numberOfSixJs = 0
    numberOf36SixJs = 0
    zeroJIndices = 0
    numberOfIndices = 0
    for keqn,eqnAll in enumerate(equations):

        # Continue
        if selectEqn and keqn != keqnMaster: continue

        # Informations about LHS and all terms of the corresponding equation
        keqnLHS,eqn = eqnAll

        # Tex, I, J, scalar for LHS
        keqnTex,keqnI,keqnJ,kScalar,extIndices = keqnLHS

        TEX.addString((r'\section{{Equation {}}}''\n').format(keqn))

        # Loop over the terms
        for kterm,term in enumerate(eqn):

            # Continue
            if selectTerm and kterm != ktermMaster: continue

            # Get necessary information for the creation of particle indices
            amplitudes = term[2]
            sumIndices = []
            for amp in amplitudes:
                ampIndices = amp[4]
                sumIndices.extend([idx for idx in ampIndices if idx not in extIndices and idx not in sumIndices])
            sumIndices.sort()
            drudgeindices = copy(extIndices)
            drudgeindices.extend(sumIndices)

            # Do smart permutations
            if doSmartPermutations:
                prelimPerm = []
                alreadyPlaced = []
                smartPermutations(prelimPerm,alreadyPlaced,extIndices,keqnI,amplitudes)

            # Get amplitudes I,J for permutations
            ampPermutations = []
            for kamp,amp in enumerate(amplitudes):

                # Amplitudes I,J
                ampI = amp[1]
                ampJ = amp[2]

                # Append to the list
                if doSmartPermutations:
                    ampPermutations.append(ampI-alreadyPlaced[2*kamp])
                    ampPermutations.append(ampJ-alreadyPlaced[2*kamp+1])
                else:
                    ampPermutations.append(ampI)
                    ampPermutations.append(ampJ)

            # Permutation loop
            if doPermutations:
                ampPermutations = [ampPermutations[len(ampPermutations)-1-i] for i in range(len(ampPermutations))]
                ampPartitions = partition(ampPermutations)
            else:
                trivialPerm = []
                for ampIJ in ampPermutations:
                    trivialPerm.append(list(range(ampIJ)))
                ampPartitions = [trivialPerm]
            sixjPerm = -1
            sixj36Perm = -1
            zerojPerm = -1
            indicesPerm = -1

            # Initialize performed permutation
            kperm_performed = -1

            for kperm,permutation in enumerate(ampPartitions):

                # Continue
                if selectPerm and kperm != kpermMaster: continue

                # Performed permutation
                kperm_performed += 1

                # Some terminal output
                if verbose:
                    if keqn != 0 and kterm != 0 and kperm == 0:
                        stdout.write("\n%1i %3i %7i / %7i" % (keqn,kterm,kperm+1,len(ampPartitions)))
                    else:
                        stdout.write("\r%1i %3i %7i / %7i" % (keqn,kterm,kperm+1,len(ampPartitions)))
                    stdout.flush()

                # Create a zero index
                zeroIdx = Idx('int',None,_jtex='0',_mtex='0',_zero=True)

                # Create the list of particle indices and summation indices
                sums = []
                partindices = []
                for drudgeIdx in drudgeindices:
                    if drudgeIdx in extIndices:
                        clbIdx = Idx('hint',_tex='{k}_{%i}'%(drudgeIdx),_external=True)
                    if drudgeIdx in sumIndices:
                        clbIdx = Idx('hint',_tex='{k}_{%i}'%(drudgeIdx))
                        sums.append(clbIdx)
                    partindices.append(clbIdx)

                # Get prefactor and amplitudes
                prefactor = Rational(term[0],term[1])
                newAmplitudes = []
                for amp in amplitudes:

                    # Amplitudes LaTeX symbol, I, J and indices
                    ampSymb = amp[0]
                    ampI = amp[1]
                    ampJ = amp[2]
                    ampScalar = amp[3]
                    ampIndices = [partindices[tensorIdx-1] for tensorIdx in amp[4]]

                    # Append to the list
                    newAmplitudes.append(MTensor(ampIndices,ampI,ampJ,ampSymb,ampScalar))

                # Permute
                signature = 1
                if doSmartPermutations:
                    signature *= applyPermutation(newAmplitudes,prelimPerm)
                signature *= applyPermutation(newAmplitudes,permutation)

                # Multiply prefactor by signature
                prefactor = prefactor * signature

                # In the case of fatal error
                # Save at least the first permutation LHS
                if kperm_performed == 0:
                    kpermSave = kperm
                    prefactorSave = prefactor
                    sumsSave = sums
                    newAmplitudesSave = newAmplitudes

                # Create fake amplitude for "external" indices
                tensorId = 0
                tensorId2 = 0
                amp0msch = MTensor(partindices[:keqnI+keqnJ],keqnI,keqnJ,keqnTex,kScalar)
                amp0 = JTensor(amp0msch,tensorId,tensorId2,_external=True)

                # First term
                clebsches = []
                interIndices = []
                fakeIndices = []
                tensorIndices = []
                clebsches.extend(amp0.getClebsches())
                interIndices.extend(amp0.interIndices)
                fakeIndices.extend(amp0.interIndices)
                if amp0.diagonalIdx != None:
                    interIndices.append(amp0.diagonalIdx)
                    fakeIndices.append(amp0.diagonalIdx)
                if amp0.diagonalIdx2 != None:
                    interIndices.append(amp0.diagonalIdx2)
                    fakeIndices.append(amp0.diagonalIdx2)
                if amp0.tensorIdx != None:
                    interIndices.append(amp0.tensorIdx)
                    fakeIndices.append(amp0.tensorIdx)

                # Jhat factor from the coupling of the LHS
                # Summation over diagonal M because considered tensors are not dependent on it
                # Convention not wigner eckart 1/jhat^2
                # Convention wigner eckart 1/jhat (see p. 132 of thesis)
                # but already included when get the CG coefficient
                if amp0.scalar:
                    if amp0.rank == 2:
                        amp0.indices[0].jhat -= 2
                    if amp0.rank >= 4:
                        amp0.diagonalIdx.jhat -= 2

                # Convert MScheme amplitudes into JScheme amplitudes
                jAmplitudes = []
                for amp in newAmplitudes:
                    if amp.rank >= 4:
                        tensorId += 1
                    if not amp.scalar:
                        tensorId2 += 1
                    jAmplitudes.append(JTensor(amp,tensorId,tensorId2))

                # Add the corresponding intermediate indices and clebsches
                for k,amp in enumerate(jAmplitudes):
                    interIndices.extend(amp.interIndices)
                    if amp.diagonalIdx != None:
                        interIndices.append(amp.diagonalIdx)
                    if amp.diagonalIdx2 != None:
                        interIndices.append(amp.diagonalIdx2)
                    if amp.tensorIdx != None:
                        interIndices.append(amp.tensorIdx)
                        tensorIndices.append(amp.tensorIdx)
                    clebsches.extend(amp.getClebsches())

                # Special case: Add clebsches of tensorial product
                if len(tensorIndices)==2:
                    clebsches.append(ClebschGordan([tensorIndices[0],tensorIndices[1],amp0.tensorIdx],[1,1,1]))

                # Tensorial "Lambda" indices are not summed over
                fakeIndices.extend(tensorIndices)

                # Replace None index in clebsches by zeroIdx
                for clb in clebsches:
                    for k,idx in enumerate(clb.indices):
                        if idx == None:
                            clb.indices[k] = zeroIdx

                # Gather indices
                indices = []
                indices.append(zeroIdx)
                indices.extend(partindices)
                indices.extend(interIndices)

                # Proceed to Yutsis graph reduction
                Y = YutsisReduction(indices,clebsches,zeroIdx)

                # If not fully reduced (higher than square not implemented) then continue
                if Y.getNumberOfNodes() != 0:
                    print("Error: Yutsis graph not fully reduced so continue")
                    continue

                # /!\ ninej (optimization does not account for ninej)
                # /!\ should be done before the addition of additional indices to indices list
                if factorize_ninej:
                    Y.factorize_ninejs()
                #if factorize_twelvej:
                #    Y.factorize_twelvejfirsts()

                # Add Y.additionalIndices to indices and interIndices
                interIndices.extend(Y.additionalIndices)
                indices.extend(Y.additionalIndices)

                # Reduction of the deltas
                deltaReduction(Y,jAmplitudes)

                # Six J Symbols canocalization
                # /!\ should be done before factorization
                for sixj in Y.sixjs:
                    sixj.canonicalize()

                # Add additional indices to sums
                sums2 = [idx for idx in interIndices if idx not in fakeIndices]

                # Condition to keep a particular permutation
                zerojTemp = 0
                for amp in jAmplitudes:
                    if amp.diagonalIdx == zeroIdx:
                        zerojTemp += 1
                indicesTemp = 0
                for idx in indices:
                    idx.simplify()
                    if idx.jphase != 0:
                        indicesTemp += 1
                sixj36Temp = 0
                for sixj in Y.sixjs:
                    nint = 0
                    for idx in sixj.indices:
                        if idx.type == 'int':
                            nint += 1
                    if nint in [3,6]:
                        sixj36Temp += 1

                #opt4
                if sixjPerm == -1 or sixj36Perm > sixj36Temp \
                        or (sixj36Perm == sixj36Temp and sixjPerm > len(Y.sixjs)) \
                        or (sixj36Perm == sixj36Temp and sixjPerm == len(Y.sixjs) and zerojPerm < zerojTemp) \
                        or (sixj36Perm == sixj36Temp and sixjPerm == len(Y.sixjs) and zerojPerm == zerojTemp and indicesPerm > indicesTemp):
                    sixjPerm = len(Y.sixjs)
                    sixj36Perm = sixj36Temp
                    zerojPerm = zerojTemp
                    indicesPerm = indicesTemp
                    kpermSave = kperm
                    prefactorSave = prefactor
                    sumsSave = sums
                    newAmplitudesSave = newAmplitudes
                    YSave = Y
                    indicesSave = indices
                    sums2Save = sums2
                    jAmplitudesSave = jAmplitudes

            # All permutations contain at least a pentagon or higher
            if sixjPerm == -1:
                fatalErrorNumb += 1
                print("Fatal error: All permutations of %i, %i contain at least a pentagon or higher"%(keqn,kterm))

                # Print Latex
                # Left Hand Side
                TEX.addString('$\\left(%s\\right)_{%i}$:\n'%(amp0msch,kterm+1))
                TEX.addString("\\begin{align}\n")
                TEX.generateLHS(prefactorSave,sumsSave,newAmplitudesSave)
                # Right Hand Side
                TEX.addString("\n")
                TEX.addString("\\end{align}\n\n")
            else:
                # Some additional informations
                numberOfSixJs += sixjPerm
                numberOf36SixJs += sixj36Perm
                zeroJIndices += zerojPerm
                numberOfIndices += indicesPerm

                # Print Latex
                # Left Hand Side
                TEX.addString('$\\left(%s\\right)_{%i}$:\n'%(amp0msch,kterm+1))
                TEX.addString("\\begin{align}\n")
                TEX.generateLHS(prefactorSave,sumsSave,newAmplitudesSave)
                # Right Hand Side
                TEX.generateRHS(YSave,prefactorSave,sumsSave,indicesSave,sums2Save,jAmplitudesSave,noThreeJ = not print_threej)
                TEX.addString("\n")
                TEX.addString("\\end{align}\n\n")

    # Write Latex file
    TEX.writeLatexFile()

    # Print number of sixj
    if verbose:
        print("")
        print("numberOfSixJs   = %s"%(numberOfSixJs))
        print("numberOf36SixJs = %s"%(numberOf36SixJs))
        print("zeroJIndices    = %s"%(zeroJIndices))
        print("numberOfIndices = %s"%(numberOfIndices))
        print("fatalErrorNumb  = %s"%(fatalErrorNumb))
        print("kpermSave       = %s"%(kpermSave))

