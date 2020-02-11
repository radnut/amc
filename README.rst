AMC
===

.. image:: https://img.shields.io/readthedocs/amc
   :alt: Read the Docs
   :target: https://amc.readthedocs.io/en/latest/
.. image:: https://img.shields.io/pypi/v/amc
   :alt: PyPI version
   :target: https://pypi.org/project/amc/
.. image:: https://img.shields.io/pypi/l/amc
   :alt: PyPI license
   :target: https://choosealicense.com/licenses/gpl-3.0/
.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3663058.svg
   :target: https://doi.org/10.5281/zenodo.3663058

In quantum many-body theory, one often encounters problems with rotational
symmetry. While methods are most conveniently derived in schemes that do not
exploit the symmetry, a symmetry-adapted formulation can lead to orders of
magnitude savings in computation time. However, actually reducing the formulas
of a many-body method to symmetry-adapted form is tedious and error-prone.

The AMC package aims to help practitioners by automating the reduction
process. The unreduced (m-scheme) equations can be entered via an easy-to-use
language. The package then uses Yutsis graph techniques to reduce the
resulting network of angular-momentum variables to irreducible Wigner 6j and
9j symbols, and outputs the reduced equations as a LaTeX file. Moreover, the
package is based on abstract representations of the unreduced and reduced
equations in the form of syntax trees, which enable other uses such as
automatic generation of code that computes the reduced equations.

Installation
------------
Install amc using the `pip <https://pip.pypa.io/en/stable/>`_ package manager.

.. code-block:: bash

    pip install amc

Usage
-----
Prepare a file with the properties of the tensors and the equations to reduce.
For example, second-order many-body perturbation theory can be reduced in this
way:

.. code-block:: none

    # mbpt.amc

    declare E2 {
        mode=0,
        latex="E^{(2)}_{0}",
    }

    # Hamiltonian
    declare H {
        mode=4,
        latex="H",
    }

    E2 = 1/4 * sum_abij(H_abij * H_ijab);

Then run the ``amc`` program on the input

.. code-block:: bash

    amc -o mbpt.tex mbpt.amc

The result is

.. math::

    E^{(2)}_{0} = \frac{1}{4} \sum_{a b i j {J}_{0}} \hat{J}_{0}^{2} H_{a b i j}^{{J}_{0} {J}_{0} 0} H_{i j a b}^{{J}_{0} {J}_{0} 0}

See the `User's Guide <https://amc.readthedocs.io/en/latest/ug.html>`__ for details.

Contributing
------------
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

License
-------
`GPLv3 <https://choosealicense.com/licenses/gpl-3.0/>`__
