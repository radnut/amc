from __future__ import (division, absolute_import, print_function)


class Delta:
    """Delta class"""

    def __init__(self, idx1, idx2):
        """Constructor method"""

        if idx1.type != idx2.type:
            raise ValueError('Indices must have same type.')

        # Tuple of two indices
        self.indices = [idx1, idx2]

        # Sort according to tex of jtex
        self.sort_indices()

    def sort_indices(self):
        """Sort indices"""

        self.indices.sort(key=lambda idx: ((0 if idx.zero else 1), (0 if idx.external else 1), idx.name))

    def apply(self):
        """Apply the delta"""

        self.indices[0].jphase += self.indices[1].jphase
        self.indices[0].mphase += self.indices[1].mphase
        self.indices[0].sign *= self.indices[1].sign
        self.indices[0].jhat += self.indices[1].jhat
        self.indices[1].set_default()

    def __str__(self):
        """String"""

        stringTemplate = r'\delta_{%s %s}'
        return stringTemplate % (self.indices[0].name, self.indices[1].name)
