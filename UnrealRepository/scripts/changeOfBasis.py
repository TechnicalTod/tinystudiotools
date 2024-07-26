import numpy as np

np.set_printoptions(precision=3)
np.set_printoptions(suppress=True)


def change_xform(source_xform, change_of_basis):
    """
    Change a transformation matrix from one coordinate to another
    https://youtu.be/P2LTAUO1TdA
    M_new = M_cob * M_source * inverse(M_cob)
    :param source_xform: numpy.ndarray. original transformation matrix
    :param change_of_basis: numpy.ndarray. change of basis matrix
    :return: converted transformation matrix in new coordinate system
    """
    inverse_change_of_basis = np.linalg.inv(change_of_basis)
    temp = np.matmul(change_of_basis, source_xform)

    return np.matmul(temp, inverse_change_of_basis)