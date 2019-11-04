#!/usr/bin/env python3

from copy import copy
from sympy import Rational
from sys import stdout
from amc.AMCFunctions import deltaReduction,partition,applyPermutation
from amc.AMCLatexFile import AMCLatexFile
from amc.JTensor import JTensor
from amc.MTensor import MTensor
from amc.YutsisGraph import Idx,YutsisReduction

def AMCReduction(equations, outputFileName, doPermutations=False, doSmartPermutations=False, verbose=False, print_threej=False, keqnMaster=None, ktermMaster=None, kpermMaster=None):
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

        # Tex, I and J for LHS
        #/!\ kScalar
        if len(keqnLHS) == 4:
            keqnTex,keqnI,keqnJ,extIndices = keqnLHS
            kScalar = True
        else:
            keqnTex,keqnI,keqnJ,extIndices,kScalar = keqnLHS

        TEX.addString((r'\section{{Equation {}}}''\n').format(keqn))

        # Loop over the terms
        for kterm,term in enumerate(eqn):

            # Continue
            if selectTerm and kterm != ktermMaster: continue

            # Get necessary information for the creation of particle indices
            amplitudes = term[2]
            sumIndices = []
            for amp in amplitudes:
                ampIndices = amp[3]
                sumIndices.extend([idx for idx in ampIndices if idx not in extIndices and idx not in sumIndices])
            sumIndices.sort()
            drudgeindices = copy(extIndices)
            drudgeindices.extend(sumIndices)

            # Do smart permutations
            if doSmartPermutations:

                # Add Left and Right indices of the LHS tensor
                allIndices = [extIndices[:keqnI],extIndices[keqnI:]]

                # Loop over RHS tensors
                for amp in amplitudes:

                    # Amplitude I, J and indices
                    ampI = amp[1]
                    ampJ = amp[2]
                    ampIndices = amp[3]

                    # Add Left and Right indices of the tensor
                    allIndices.append(ampIndices[:ampI])
                    allIndices.append(ampIndices[ampI:])

                prelimPerm = [list(range(len(amp))) for amp in allIndices[2:]]
                alreadyPlaced = [0 for amp in allIndices[2:]]
                for kamp1,amp1 in enumerate(allIndices):

                    # If already treated once then no other treatment
                    if kamp1-2 >= 0 and alreadyPlaced[kamp1-2] != 0:
                        continue

                    # I,J
                    ampI1,ampJ1 = len(allIndices[kamp1-kamp1%2]),len(allIndices[kamp1-kamp1%2+1])

                    for kamp2,amp2 in enumerate(allIndices):

                        # Consider all couples only one time
                        if kamp2 < kamp1+1+(kamp1+1)%2:
                            continue

                        # If already treated once then no other treatment
                        if kamp1-2 >= 0 and alreadyPlaced[kamp1-2] != 0:
                            break

                        # If already treated once then no other treatment
                        if kamp2-2 >= 0 and alreadyPlaced[kamp2-2] != 0:
                            continue

                        # I,J
                        ampI2,ampJ2 = len(allIndices[kamp2-kamp2%2]),len(allIndices[kamp2-kamp2%2+1])

                        # Get list of common indices
                        common = []
                        for idx1 in amp1:
                            for idx2 in amp2:
                                if idx1 == idx2:
                                    common.append(idx1)

                        # Amplitude 0 left part
                        # Can not be permuted so dictates the permutation of the other amplitude
                        if kamp1 == 0:

                            ## Two-body external
                            ##40 k1 k2 | k3 k4 0 1 2 3
                            ##31 k1 k2 | k3    0 1
                            ##22 k1 k2 |       0 1
                            ##13 k1    |        no
                            ##04       |        no
                            #if ampI1+ampJ1 == 4:
                            #    if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                            #        common = amp1[0:2]
                            #    elif ampI1 >= 4 and amp1[2] in common and amp1[3] in common:
                            #        common = amp1[2:4]
                            #    else:
                            #        common = []

                            ## Three-body external
                            ##60 k1 k2 k3 | k4 k5 k6 0 1 3 4
                            ##51 k1 k2 k3 | k4 k5    0 1 3 4
                            ##42 k1 k2 k3 | k4       0 1
                            ##33 k1 k2 k3 |          0 1
                            ##24 k1 k2    |          0 1
                            ##15 k1       |           no
                            ##06          |           no
                            #if ampI1+ampJ1 == 6:
                            #    if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                            #        common = amp1[0:2]
                            #    elif ampI1 >= 5 and amp1[3] in common and amp1[4] in common:
                            #        common = amp1[3:5]
                            #    else:
                            #        common = []

                            # A-body external
                            if ampI1+ampJ1 >= 4:
                                if ampI1 >= 2 and amp1[0] in common and amp1[1] in common:
                                    common = amp1[0:2]
                                elif ampI1 >= (ampI1+ampJ1)//2 + 2 and amp1[(ampI1+ampJ1)//2] in common and amp1[(ampI1+ampJ1)//2+1] in common:
                                    common = amp1[(ampI1+ampJ1)//2:(ampI1+ampJ1)//2+2]
                                else:
                                    common = []

                        elif kamp1 == 1:

                            ## Two-body external
                            ##40       |        no
                            ##31       |    k1  no
                            ##22       | k1 k2 0 1
                            ##13    k1 | k2 k3 1 2
                            ##04 k1 k2 | k3 k4 2 3 0 1
                            #if ampI1+ampJ1 == 4:
                            #    if ampJ1 >= 2 and amp1[ampJ1-2] in common and amp1[ampJ1-2+1] in common:
                            #        common = amp1[ampJ1-2:ampJ1]
                            #    elif ampJ1 >= 4 and amp1[ampJ1-4] in common and amp1[ampJ1-4+1] in common:
                            #        common = amp1[ampJ1-4:ampJ1-2]
                            #    else:
                            #        common = []

                            ## Three-body external
                            ##60          |           no
                            ##51          |       k1  no
                            ##42          |    k1 k2  no
                            ##33          | k1 k2 k3 0 1
                            ##24       k1 | k2 k3 k4 1 2
                            ##15    k1 k2 | k3 k4 k5 2 3
                            ##06 k1 k2 k3 | k4 k5 k6 3 4 0 1
                            #if ampI1+ampJ1 == 6:
                            #    if ampJ1 >= 3 and amp1[ampJ1-3] in common and amp1[ampJ1-3+1] in common:
                            #        common = amp1[ampJ1-3:ampJ1-1]
                            #    elif ampJ1 >= 6 and amp1[ampJ1-6] in common and amp1[ampJ1-6+1] in common:
                            #        common = amp1[ampJ1-6:ampJ1-4]
                            #    else:
                            #        common = []

                            # A-body external
                            if ampI1+ampJ1 >= 4:
                                if ampJ1 >= (ampI1+ampJ1)//2 and amp1[ampJ1-(ampI1+ampJ1)//2] in common and amp1[ampJ1-(ampI1+ampJ1)//2+1] in common:
                                    common = amp1[ampJ1-(ampI1+ampJ1)//2:ampJ1-(ampI1+ampJ1)//2+2]
                                elif ampJ1 >= (ampI1+ampJ1) and amp1[ampJ1-(ampI1+ampJ1)] in common and amp1[ampJ1-(ampI1+ampJ1)+1] in common:
                                    common = amp1[ampJ1-(ampI1+ampJ1):ampJ1-(ampI1+ampJ1)+2]
                                else:
                                    common = []

                        # If at least two common indices
                        if len(common) >= 2:

                            # Get position of common indices
                            perm1 = []
                            perm2 = []
                            for k in range(2):
                                for k1,idx1 in enumerate(amp1):
                                    if idx1 == common[k]:
                                        perm1.append(k1)
                                        break
                                for k2,idx2 in enumerate(amp2):
                                    if idx2 == common[k]:
                                        perm2.append(k2)
                                        break

                            # If LHS for amp1
                            if kamp1%2 == 0:
                                # Indices fixed to the left and other to the right
                                perm1.extend([k for k in range(ampI1) if k not in perm1])

                            # Else RHS for amp1
                            else:
                                if ampI1 >= (ampI1+ampJ1)//2:
                                    # Indices fixed to the left and other to the right
                                    perm1.extend([k for k in range(ampJ1) if k not in perm1])
                                else:
                                    # Indices fixed after rank//2
                                    temp = [k for k in range(ampJ1) if k not in perm1]
                                    temp2 = temp[:(ampI1+ampJ1)//2-ampI1]
                                    temp2.extend(perm1)
                                    temp2.extend(temp[(ampI1+ampJ1)//2-ampI1:])
                                    perm1 = temp2

                            # If LHS for amp2
                            if kamp2%2 == 0:
                                # Indices fixed to the left and other to the right
                                perm2.extend([k for k in range(ampI2) if k not in perm2])

                            # Else RHS for amp2
                            else:
                                if ampI2 >= (ampI2+ampJ2)//2:
                                    # Indices fixed to the left and other to the right
                                    perm2.extend([k for k in range(ampJ2) if k not in perm2])
                                else:
                                    # Indices fixed after rank//2
                                    temp = [k for k in range(ampJ2) if k not in perm2]
                                    temp2 = temp[:(ampI2+ampJ2)//2-ampI2]
                                    temp2.extend(perm2)
                                    temp2.extend(temp[(ampI2+ampJ2)//2-ampI2:])
                                    perm2 = temp2

                            # If not the LHS amplitude then save the permutation
                            if kamp1-2 >= 0:
                                prelimPerm[kamp1-2] = perm1
                                alreadyPlaced[kamp1-2] +=2
                            if kamp2-2 >= 0:
                                prelimPerm[kamp2-2] = perm2
                                alreadyPlaced[kamp2-2] +=2


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

            ## Remove T1,H20,H02 and T3 amplitude for now
            #doContinue = False
            #for k in range(len(ampPermutations)//2):
            ##    if amp.rank == 2 and amp.I != 1:
            ##        doContinue = True
            ##        break
            #    if ampPermutations[2*k] + ampPermutations[2*k+1] == 6:
            #        doContinue = True
            #        break
            #if doContinue:
            #    continue

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
                    ampIndices = [partindices[tensorIdx-1] for tensorIdx in amp[3]]
                    #/!\ not that good...
                    ampScalar = amp[4] if len(amp)==5 else True

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
                #/!\ convention not wigner eckart (with wigner eckart -1 instead of -2, see p. 132 of thesis)
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

                #/!\ Special case
                # Add clebsches of tensorial product
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

                # Add Y.additionalIndices to indices and interIndices
                interIndices.extend(Y.additionalIndices)
                indices.extend(Y.additionalIndices)

                # Reduction of the deltas
                deltaReduction(Y,jAmplitudes)

                # Six J Symbols canocalization
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

