"""
This file contains utilities to work with autodock vina.
"""
from typing import List, Optional, Tuple

import numpy as np
from deepchem.utils.typing import RDKitMol
from deepchem.utils.pdbqt_utils import pdbqt_to_pdb


def write_vina_conf(protein_filename: str,
                    ligand_filename: str,
                    centroid: np.ndarray,
                    box_dims: np.ndarray,
                    conf_filename: str,
                    num_modes: int = 9,
                    exhaustiveness: int = None) -> None:
  """Writes Vina configuration file to disk.

  Autodock Vina accepts a configuration file which provides options
  under which Vina is invoked. This utility function writes a vina
  configuration file which directions Autodock vina to perform docking
  under the provided options.

  Parameters
  ----------
  protein_filename : str
    Filename for protein
  ligand_filename : str
    Filename for the ligand
  centroid : np.ndarray
    A numpy array with shape `(3,)` holding centroid of system
  box_dims : np.ndarray
    A numpy array of shape `(3,)` holding the size of the box to dock
  conf_filename : str
    Filename to write Autodock Vina configuration to.
  num_modes : int, optional (default 9)
    The number of binding modes Autodock Vina should find
  exhaustiveness : int, optional
    The exhaustiveness of the search to be performed by Vina
  """
  with open(conf_filename, "w") as f:
    f.write("receptor = %s\n" % protein_filename)
    f.write("ligand = %s\n\n" % ligand_filename)

    f.write("center_x = %f\n" % centroid[0])
    f.write("center_y = %f\n" % centroid[1])
    f.write("center_z = %f\n\n" % centroid[2])

    f.write("size_x = %f\n" % box_dims[0])
    f.write("size_y = %f\n" % box_dims[1])
    f.write("size_z = %f\n\n" % box_dims[2])

    f.write("num_modes = %d\n\n" % num_modes)
    if exhaustiveness is not None:
      f.write("exhaustiveness = %d\n" % exhaustiveness)


def load_docked_ligands(
    pdbqt_output: str) -> Tuple[List[RDKitMol], List[float]]:
  """This function loads ligands docked by autodock vina.

  Autodock vina writes outputs to disk in a PDBQT file format. This
  PDBQT file can contain multiple docked "poses". Recall that a pose
  is an energetically favorable 3D conformation of a molecule. This
  utility function reads and loads the structures for multiple poses
  from vina's output file.

  Parameters
  ----------
  pdbqt_output: str
    Should be the filename of a file generated by autodock vina's
    docking software.

  Returns
  -------
  Tuple[List[rdkit.Chem.rdchem.Mol], List[float]]
    Tuple of `molecules, scores`. `molecules` is a list of rdkit
    molecules with 3D information. `scores` is the associated vina
    score.

  Notes
  -----
  This function requires RDKit to be installed.
  """
  try:
    from rdkit import Chem
  except ModuleNotFoundError:
    raise ValueError("This function requires RDKit to be installed.")

  lines = open(pdbqt_output).readlines()
  molecule_pdbqts = []
  scores = []
  current_pdbqt: Optional[List[str]] = None
  for line in lines:
    if line[:5] == "MODEL":
      current_pdbqt = []
    elif line[:19] == "REMARK VINA RESULT:":
      words = line.split()
      # the line has format
      # REMARK VINA RESULT: score ...
      # There is only 1 such line per model so we can append it
      scores.append(float(words[3]))
    elif line[:6] == "ENDMDL":
      molecule_pdbqts.append(current_pdbqt)
      current_pdbqt = None
    else:
      # FIXME: Item "None" of "Optional[List[str]]" has no attribute "append"
      current_pdbqt.append(line)  # type: ignore

  molecules = []
  for pdbqt_data in molecule_pdbqts:
    pdb_block = pdbqt_to_pdb(pdbqt_data=pdbqt_data)
    mol = Chem.MolFromPDBBlock(str(pdb_block), sanitize=False, removeHs=False)
    molecules.append(mol)
  return molecules, scores
