import re
import openbabel as ob
import cmd_pymol
import random
import numpy as np

class PymolInterface:


    def __init__(self):
        self.cmd = cmd_pymol.CMDPymol()
        # Atom selection mode
        self.cmd.set("mouse_selection_mode", 0)
        self.space = {"default_color" : {},
                      "atom_names": {}}

    def get_random_color(self):
        choice = random.choice(self.cmd.get_color_indices())
        while choice in self.space["default_color"].values():
            choice = random.choice(self.cmd.get_color_indices())
        return choice

    # Move style-related calls to outside and create _optimize() function
    def optimize_molecule_geometry (self, selection='all', forcefield='MMFF94s', method='steepest-descent', nsteps1= 1000, conv=0.000001, cutoff=False, cut_vdw=4.0, cut_elec=8.0):
        #TODO: Do this before, when the molecule is downloaded
        self.cmd.iterate(selection, "default_color[name] = color", space=self.space)
        self.space["atom_names"] = {}
        self.cmd.iterate_state(0, selection, "atom_names[index] = name", space=self.space)
        name = self.cmd.get_legal_name(selection)
        self.cmd.alter(name, "name = elem")
        #If a potential atom has been asigned it will show up format NAME(ID), but openbabel
        # cannot handle names with more than 4 characters.
        pdb_string = self.cmd.get_pdbstr(name)
        obconversion = ob.OBConversion()
        obconversion.SetInAndOutFormats('pdb', 'pdb')
        mol = ob.OBMol()
        obconversion.ReadString(mol, pdb_string)
        mol.AddHydrogens()
        ff = ob.OBForceField.FindForceField(forcefield) ## GAFF, MMFF94s, MMFF94, UFF, Ghemical
        ff.Setup(mol)
        if cutoff is True:
            ff.EnableCutOff(True)
            ff.SetVDWCutOff(cut_vdw)
            ff.SetElectrostaticCutOff(cut_elec)
        if method == 'steepest-descent':
            ff.SteepestDescent(nsteps1, conv)
        else:
            ff.ConjugateGradients(nsteps1, conv)
        ff.GetCoordinates(mol)
        nrg = ff.Energy()
        pdb_string = obconversion.WriteString(mol)
        self.cmd.delete(name)
        if name == 'all':
            name = 'all_'
        self.cmd.read_pdbstr(pdb_string, name)
        self.cmd.alter(name, "name = atom_names[index]", space=self.space)
        self._apply_default_style()
        print '#########################################'
        print 'The Energy of %s is %8.2f %s       '  % (name, nrg, ff.GetUnit())
        print '#########################################'

    def conf_search(self, selection='all', forcefield='MMFF94s', method='Weighted', nsteps1= 100, conformers=25, lowest_conf=5):
        self.cmd.iterate(selection, "default_color[name] = color", space=self.space)
        self.space["atom_names"] = {}
        self.cmd.iterate_state(0, selection, "atom_names[index] = name", space=self.space)
        name = self.cmd.get_legal_name(selection)
        # Pdb cannot accept names of more then 4 characters
        self.cmd.alter(name, "name = elem")
        
        pdb_string = self.cmd.get_pdbstr(selection)
        obconversion = ob.OBConversion()
        obconversion.SetInAndOutFormats('pdb', 'pdb')
        mol = ob.OBMol()
        obconversion.ReadString(mol, pdb_string)
        mol.AddHydrogens()
        ff = ob.OBForceField.FindForceField(forcefield) ## GAFF, MMFF94s, MMFF94, UFF, Ghemical
        ff.Setup(mol)
        if method == 'Weighted':
            ff.WeightedRotorSearch(conformers, nsteps1)
        elif method == 'Random':
            ff.RandomRotorSearch(conformers, nsteps1)
        else:
            ff.SystematicRotorSearch(nsteps1)
        if name == 'all':
            name = 'all_'
        if method in ['Weighted', 'Random']:
            ff.GetConformers(mol)
            print '##############################################'
            print '   Conformer    |         Energy      |  RMSD'
            nrg_unit = ff.GetUnit()
            rmsd = 0
            ff.GetCoordinates(mol)
            nrg = ff.Energy()
            conf_list = []
            for i in range(conformers):
                mol.SetConformer(i) 
                ff.Setup(mol)
                nrg = ff.Energy()
                conf_list.append((nrg, i))
            conf_list.sort()
            lenght_conf_list = len(conf_list)
            if lowest_conf > lenght_conf_list:
                lowest_conf = lenght_conf_list
            for i in range(lowest_conf):
                nrg, orden = conf_list[i]
                name_n = '%s%02d' % (name, i)
                self.cmd.delete(name_n)
                mol.SetConformer(orden) 
                #pdb_string = obconversion.WriteString(mol)
                #self.cmd.read_pdbstr(pdb_string, name_n)
                if i != 0:
                    rmsd = self.cmd.fit(name_n, '%s00' % name, quiet=1)
                print '%15s | %10.2f%9s |%6.1f'    % (name_n, nrg, nrg_unit, rmsd)
            print '##############################################'
        else:
            ff.GetCoordinates(mol)
            nrg = ff.Energy()
            pdb_string = obconversion.WriteString(mol)
            self.cmd.delete(name)
            self.cmd.read_pdbstr(pdb_string, name)
            print '#########################################'
            print 'The Energy of %s is %8.2f %s       '  % (name, nrg, ff.GetUnit())
            print '#########################################'

        nrg, orden = conf_list[0]
        self.cmd.delete(name)
        mol.SetConformer(orden)
        pdb_string = obconversion.WriteString(mol)
        self.cmd.read_pdbstr(pdb_string, name)
        self.cmd.alter(name, "name = atom_names[index]", space=self.space)
        self._apply_default_style()
        




    def _apply_default_style(self):
        self.cmd.alter("all", "color = " + "default_color.get((name), color)", space=self.space)
        self.cmd.label("all", "name")
        self.cmd.set("label_color","white")
        self.cmd.hide("lines")
        self.cmd.show("sticks")
        self.cmd.show("spheres")
        self.cmd.set("stick_radius", "0.1")
        self.cmd.set("sphere_scale", "0.25")

    def match_elem2name(self):
        self.cmd.alter("all", "name = name.split('(')[0]")
        self.cmd.label("all", "name")

    def load_molecule(self, fname):
        self.cmd.load(fname)
        # Default configuration
        self._apply_default_style()
        # Save default color assigned
        self.cmd.iterate("all", "default_color[name] = color", space=self.space)


    def get_molecule_model(self):
        return self.cmd.get_model()

    def get_molecule_name(self):
        return self.cmd.get_names()[0]

    @staticmethod
    def _index_from_name(at_name):
        ret = ""
        try:
            ret = at_name.split("(")[1].split(")")[0]
        except:
            return at_name
        return ret
        

    #TODO: Allo 2nd neighbors to be used to associate names and define a grammar. Get rid
    # eval/exec
    def _meet_condition(self, atom_sel, cond):
        # Get the list of element names. Remove duplicates.
        atomname_list = list(set(re.findall("[a-zA-Z]+\([0-9a-zA-Z]+\)|[a-zA-Z]+", cond)))
        
        for at_name in atomname_list:
            index = _index_from_name(at_name)
            if index == "":
                var_name = at_name
            else:
                var_name =  "%s_%s" % (at_name.split('(')[0], index)
                cond = cond.replace(at_name, var_name)
            print "sele chain: ", "(neighbor %s) & name '%s')" % (atom_sel, at_name)

            self.cmd.select("neighs","(neighbor %s)" % atom_sel)
            neighs = self.cmd.get_model("neighs")
            atom_count = 0
            for at in neighs.atom:
                print "Names: ", at.name, at_name
                if at.name == at_name:
                    atom_count += 1
            print "Atoms selected: ", atom_count
            self.cmd.delete("neighs")
            print "c: ", var_name + " = " + str(atom_count)
            exec(var_name + " = " + str(atom_count))

        cond = cond.replace("&", "and") 
        cond = cond.replace("|", "or") 
        cond = cond.replace("=", "==") 
        # If the condition is empty by default is true so every atom
        # will be renamed in change_atom_name
        print "cond: ", cond
        return bool(not cond or eval(cond))

        
    def change_atom_name_sel(self, atom_name_out, color=None):
        # Check if sele is empty
        self.cmd.iterate("all", "default_color[name] = color", space=self.space)
        if self.cmd.alter("sele", "name = '%s'" % atom_name_out) == 0:
             raise RuntimeError("Mouse selection empty!")

        if color is not None:
            self.cmd.alter("sele", "color = " + str(color[1]))

        self.cmd.sort("all")
        # move it out of this function
        self.cmd.delete("sele")
        self._apply_default_style()

    def _correct_H_bonding(self):
        atoms = self.cmd.get_model("all")
        for at in atoms.atom:
            if at.name == "H":
                self.cmd.select("at_sel", "idx. " + str(at.index))
                self.cmd.select("neighs","(neighbor at_sel)")
                atom_count = self.cmd.count_atoms("neighs")
                print "count: ", atom_count
                myspace = {"pos": []}
                self.cmd.iterate_state(0, "(neighbor at_sel)", "pos.extend([x,y,z])", space=myspace)
                v = np.array(at.coord) - np.array(myspace["pos"])
                print myspace
                print at.name, at.coord
                print v, v/np.linalg.norm(v)
                self.cmd.translate(list(v/np.linalg.norm(v) - v), "at_sel")

    def change_atom_name_cond(self, atom_name_in, atom_name_out, cond, color=None):
        atoms = self.cmd.get_model("all")
        self.cmd.iterate("all", "default_color[name] = color", space=self.space)
        atoms_changed = 0
        print atom_name_out

        for at in atoms.atom:
            if at.name == atom_name_in:
                self.cmd.select("at_sel", "idx. " + str(at.index))
                print "Name: ", at.name
                if self._meet_condition("at_sel", cond):
                    print "Condition met.", at.name
                    atoms_changed += 1 
                    self.cmd.alter("at_sel", "name = '%s'" % atom_name_out)
                    if color is not None:
                        self.cmd.alter("at_sel", "color = " + str(color[1]))


                self.cmd.delete("at_sel")

        self.cmd.sort("all")
        self._apply_default_style()
        return atoms_changed

    def save_molecule(self, fname):
        self.match_elem2name()
        self.cmd.save(fname, "all", -1)

    def shutdown(self):
        self.cmd.quit()

ELEMENTS = {
    1: 'H',
    2: 'He',
    3: 'Li',
    4: 'Be',
    5: 'B',
    6: 'C',
    7: 'N',
    8: 'O',
    9: 'F',
    10: 'Ne',
    11: 'Na',
    12: 'Mg',
    13: 'Al',
    14: 'Si',
    15: 'P',
    16: 'S',
    17: 'Cl',
    18: 'Ar',
    19: 'K',
    20: 'Ca',
    21: 'Sc',
    22: 'Ti',
    23: 'V',
    24: 'Cr',
    25: 'Mn',
    26: 'Fe',
    27: 'Co',
    28: 'Ni',
    29: 'Cu',
    30: 'Zn',
    31: 'Ga',
    32: 'Ge',
    33: 'As',
    34: 'Se',
    35: 'Br',
    36: 'Kr',
    37: 'Rb',
    38: 'Sr',
    39: 'Y',
    40: 'Zr',
    41: 'Nb',
    42: 'Mo',
    43: 'Tc',
    44: 'Ru',
    45: 'Rh',
    46: 'Pd',
    47: 'Ag',
    48: 'Cd',
    49: 'In',
    50: 'Sn',
    51: 'Sb',
    52: 'Te',
    53: 'I',
    54: 'Xe',
    55: 'Cs',
    56: 'Ba',
    57: 'La',
    58: 'Ce',
    59: 'Pr',
    60: 'Nd',
    61: 'Pm',
    62: 'Sm',
    63: 'Eu',
    64: 'Gd',
    65: 'Tb',
    66: 'Dy',
    67: 'Ho',
    68: 'Er',
    69: 'Tm',
    70: 'Yb',
    71: 'Lu',
    72: 'Hf',
    73: 'Ta',
    74: 'W',
    75: 'Re',
    76: 'Os',
    77: 'Ir',
    78: 'Pt',
    79: 'Au',
    80: 'Hg',
    81: 'Tl',
    82: 'Pb',
    83: 'Bi',
    84: 'Po',
    85: 'At',
    86: 'Rn',
    87: 'Fr',
    88: 'Ra',
    89: 'Ac',
    90: 'Th',
    91: 'Pa',
    92: 'U',
    93: 'Np',
    94: 'Pu',
    95: 'Am',
    96: 'Cm',
    97: 'Bk',
    98: 'Cf',
    99: 'Es',
    100: 'Fm',
    101: 'Md',
    102: 'No',
    103: 'Lr',
    104: 'Rf',
    105: 'Db',
    106: 'Sg',
    107: 'Bh',
    108: 'Hs',
    109: 'Mt',
    110: 'Ds',
    111: 'Rg',
    112: 'Cp',
    113: 'ut',
    114: 'uq',
    115: 'up',
    116: 'uh',
    117: 'us',
    118: 'uo',
}


if __name__ == "__main__":
    pymol_cmd = PymolInterface()
    pymol_cmd.load_molecule("squalane.sdf")
    pymol_cmd.change_atom_name_cond("C", "CH2", "H=2 | H = 1")
    pymol_cmd.save_molecule("molecule.sdf")
