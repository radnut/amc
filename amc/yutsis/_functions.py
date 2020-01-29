# Copyright (C) 2020  Julien Ripoche, Alexander Tichai, Roland Wirth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import (division, absolute_import, print_function)

from copy import copy

from ._graph import YutsisGraph
from ._delta import Delta


def handle_zero_lines(threejms, indices, deltas):
    """Treat zero line inside 3JM-symbols"""

    # /!\ Check here
    # /!\ Add all other possible cases

    # Consider three different checks:
    # 1) If two indices are equals then the last one is a zero line
    # 2) Treat 3JM-Symbol with one zero line and two different other indices
    # 3) Treat 3JM-Symbol with one zero line and two identical indices
    icount = 0
    check1done = True
    check2done = True
    check3done = True
    while check1done or check2done or check3done or icount > 100:

        # Increment the number of iterations
        icount += 1

        # 1) If two indices are equals then the last one is a zero line
        check1done = False
        for threejm in threejms:
            for k, idx in enumerate(threejm.indices):

                # If two indices are equals
                if threejm.indices.count(idx) == 2:

                    # Consider the other index
                    diffList = [x for x in threejm.indices if x != idx]

                    # diffList should contain only one element
                    if len(diffList) != 1:
                        print("Error: diffList should contain only one element")

                    # The last one is a zero line
                    zeroIdx = diffList[0]
                    if not zeroIdx.zero:

                        # Set index summation character to zero
                        zeroIdx.zero = True

                        # Add delta
                        deltas.append(Delta(zeroIdx, indices[0]))

                        # Check1 completed
                        check1done = True

                    break

                elif indices.count(idx) == 1:
                    pass
                elif indices.count(idx) == 3:
                    print("Error: An index should not appear three times in a 3JM-Symbol")
                else:
                    print("Error: Impossible case")

        # 2) Treat 3JM-Symbol with one zero line and two different other indices
        # ( j1  j2  0 )
        # ( m1 -m2  0 ) = \delta_{j_1 j_2} \delta{m_1 m_2} (-1)^{j_1 - m_1} / \sqrt{2j_1 + 1}
        #                             ( j1  j2  0 )
        # \sum_{m_2} (-1)^{j_2 - m_2} ( m1 -m2  0 ) f(j_2,m_2) = \delta_{j_1 j_2} f(j_1,m_1) / \sqrt{2j_1 + 1}
        check2done = False
        threejmsCopy = copy(threejms)
        for ktest, threejm in enumerate(threejmsCopy):
            for k, idx in enumerate(threejm.indices):

                # If the 3JM-Symbol contains a zero line
                if idx.zero:

                    # Put zero line to the right of the 3JM-Symbol
                    threejm.exchange(k, 2)

                    # Consider the non-zero indices
                    diffList = [x for x in threejm.indices if not x.zero]

                    # Multiple zero lines
                    if len(diffList) != 2:
                        print('Error: Not able to treat 3JM-Symbol with multiple zero lines or external lines')

                    # If non-zero indices are the same then break
                    if(diffList[0] == diffList[1]):
                        break

                    # Consider the two non-zero indices
                    idx1 = diffList[0]
                    idx2 = diffList[1]

                    # If the projections have the same signs then flip the second one
                    if threejm.signs[0] == threejm.signs[1]:

                        # Flip the m2 sign in the phase
                        idx2.mphase *= -1

                        # For each 3JM-Symbol
                        for threejmp in threejms:
                            for kp, idxp in enumerate(threejmp.indices):

                                # Flip the m2 in the projection
                                # and add the proper phase
                                if idx2 == idxp:
                                    threejmp.signs[kp] *= -1

                                    # Add the proper (-1)^{j-m} phase
                                    if threejmp.signs[kp] == -1:
                                        idx2.jphase += 1
                                        idx2.mphase -= 1

                                    # Remove the (-1)^{j+m} phase
                                    else:
                                        idx2.jphase += 1
                                        idx2.mphase += 1

                    # If first sign negative then permute two first indices
                    if threejm.signs[0] == -1:
                        threejm.exchange(0, 1)

                    # Add delta
                    deltas.append(Delta(idx1, idx2))

                    # Get surviving index
                    idx1 = deltas[-1].indices[0]
                    idx2 = deltas[-1].indices[1]

                    # Add jhat factor
                    idx1.jhat -= 1

                    # Replace idx2 by idx1 in threejms
                    for threejmp in threejms:
                        for kp, idxp in enumerate(threejmp.indices):
                            if idxp == idx2:
                                threejmp.set_idx(idx1, kp)

                    # Remove threejm
                    threejms.remove(threejm)

                    # Check2 completed
                    check2done = True

                    break

        # 3) Treat 3JM-Symbol with one zero line and two identical indices
        # ( j1  j1  0 )
        # ( m1 -m1  0 ) = (-1)^{j_1 - m_1} / \sqrt{2j_1 + 1}
        #                             ( j1  j1  0 )
        # \sum_{m_1} (-1)^{j_1 - m_1} ( m1 -m1  0 ) = \sqrt{2j_1 + 1}
        check3done = False
        threejmsCopy = copy(threejms)
        for ktest, threejm in enumerate(threejmsCopy):
            for k, idx in enumerate(threejm.indices):

                # If the 3JM-Symbol contains a zero line
                if idx.zero:

                    # Put zero line to the right of the 3JM-Symbol
                    threejm.exchange(k, 2)

                    # Consider the non-zero indices
                    diffList = list(set(threejm.indices) - set([idx]))
                    idx1 = diffList[0]
                    if len(diffList) == 2:
                        print("Error: There should not be 3JM-Symbol of this kind left")

                    # Multiple zero lines
                    if idx1.zero:
                        print('Error: Not able to treat 3JM-Symbol with multiple zero lines')

                    # If the projections have the same signs then there is an error
                    if threejm.signs[0] == threejm.signs[1]:
                        # (j1 j1 0)
                        # (m1 m1 0) => j1=0 m1=0
                        print('Error: This kind of 3JM-Symbol is not taken care of')

                    # If first sign negative then permute two first indices
                    if threejm.signs[0] == -1:
                        threejm.exchange(0, 1)

                    # Add jhat factor
                    idx1.jhat += 1

                    # Remove threejm
                    threejms.remove(threejm)

                    # Check3 completed
                    check3done = True

                    break

    # Error printing
    if icount > 100:
        print("Error: Either there is an error in the zero line treatment or icountmax is too small")
    for threejm in threejms:
        for idx in threejm.indices:
            if idx.zero:
                print("Error: There should not be zero line index left in 3JM-Symbol")


def canonicalize(threejms, indices, deltas):
    """Put the string of 3JM-symbols into canonical form"""

    # Error counter
    errorCount = 0

    # Test if some index does not appear twice
    indicesAppear = {}
    for threejm in threejms:
        for idx in threejm.indices:
            if idx in indicesAppear:
                indicesAppear[idx] += 1
            else:
                indicesAppear[idx] = 1
    for idx, idxAppear in indicesAppear.items():
        if idxAppear > 2:
            print('Error: Some indices appear more than twice')
        if idxAppear < 2:
            print('Error: Some indices appear only once')

    # Change sign of angular momentum projections in order
    # to bring the string of 3JM-symbols into canonical form
    outputList = [threejms[0]] if len(threejms) > 0 else []
    for k, threejm in enumerate(outputList):

        # Consider all 3JM-Symbol but the one of the first loop
        diffList = list(set(threejms) - set([threejm]))
        for threejmp in diffList:

            # Loop on the indices of threejm
            for i, idx in enumerate(threejm.indices):

                # Loop on the indices of threejmp
                for j, idxp in enumerate(threejmp.indices):

                    # If the two indices are the same
                    if idx == idxp:

                        # If the M projections are the same then flip the ones of threejmp
                        if threejm.get_sign(i) == threejmp.get_sign(j):
                            threejmp.flip_signs()
                            # This should not append or inconsistent string of clebsch
                            if threejmp in outputList:
                                errorCount += 1
                                print("Error: Inconsistent M projections")

                        # If threejmp not already in outputList then append
                        if threejmp not in outputList:
                            outputList.append(threejmp)

        # Non-connected graph:
        # Add another threejm to outputList and loop
        if k == len(outputList) - 1 and k != len(threejms) - 1:
            for threejm in threejms:
                if threejm not in outputList:
                    outputList.append(threejm)
                    break

    # In case of error
    if errorCount != 0:
        print("Error: In the canonicalize process")


def YutsisReduction(indices, clebsches, zeroIdx, max_iter=100):
    """Proceed to the simplification of the Yutsis graph"""

    # Transform Clebsch-Gordan coefficients into 3JM-Symbols
    threejms = []
    for clebsch in clebsches:
        threejms.append(clebsch.get_threejm())

    # Treat zero line inside 3JM-symbols
    deltas = []
    handle_zero_lines(threejms, indices, deltas)

    # Canonicalization of the string of 3JM-Symbols
    canonicalize(threejms, indices, deltas)

    # Create the Yutsis Graph
    Ymain = YutsisGraph(threejms, deltas, zeroIdx)

    # Get single internal line separated graphs
    Ymain.separate_graph()

    # Get disconnected graphs
    Ylist = Ymain.get_disconnected_graphs()

    # Loop over disconnected Yutsis graph
    addIdxId = 0
    for Y in Ylist:

        # Main graph reduction loop
        iterNum = 0

        while Y.get_number_of_nodes() > 2 and iterNum < max_iter:
            iterNum += 1
            onecycleEdges = []
            bubbleEdges = []
            triangleEdges = []
            squareEdges = []

            if Y.onecycleSearch(onecycleEdges) != []:
                print("Error: One-cycle should never appear because single internal line graph are separated")
                exit(-1)
            elif Y.bubbleSearch(bubbleEdges) != []:
                Y.bubbleReduction(bubbleEdges[0])
            elif Y.triangleSearch(triangleEdges) != []:
                Y.triangleReduction(triangleEdges[0])
            elif Y.squareSearch(squareEdges) != []:
                addIdxId += 1
                Y.squareReduction(squareEdges[0], addIdxId)
            else:
                print("Error: Bigger than square not implemented yet")
                break

        # Maximum number of iteration achieved
        if iterNum == max_iter:
            print("Error: Maximum number of iteration achieved")

        # Get the final 3J-symbol
        if Y.get_number_of_nodes() == 2:
            Y.finalTriangularDelta()

        # Yutsis graph not fully reduced
        if Y.get_number_of_nodes() != 0:
            print("Error: Yutsis graph not fully reduced")

        # Remove 3j-Symbols that are already part of a 6j-Symbol
        Y.remove_redundant_triangulardeltas()

    # Merge Yutsis graphs
    for Y in Ylist[1:]:
        Ylist[0].merge(Y)

    return Ylist[0]

