POTENTIALS = {'OPLSAA': ('oplsaa.prm', 'oplsaa.lt'),
              'LOPLSAA': ('loplsaa.prm', 'loplsaa.lt'),
              }


def get_OPLS_atom_types(potential):
    atoms = {}
    with open(POTENTIALS[potential][0], 'r') as f:
        lines = f.readlines()
        lines = list(filter(lambda l: l.startswith('atom'), lines))
        for l in lines:
            l = l.split('"')
            atom_info = l[1]
            l = l[0].split()
            atom_id = l[1]
            atom_name = l[3]
            atoms[atom_id] = (atom_name, atom_info)
    return atoms


ATOM_TYPES = {'OPLSAA': get_OPLS_atom_types('OPLSAA'),
              'LOPLSAA': get_OPLS_atom_types('LOPLSAA'),
              }


def get_model_atom_types(mol_model):
    model_atom_types = set()
    for atom in mol_model.atom:
        model_atom_types.add(atom.name)
    return list(model_atom_types)

class PackmolSystemWriter:
    def __init__(self, box_dims, molecules, system_name=''):
        self.box_xlo = box_dims[0][0]
        self.box_xhi = box_dims[0][1]
        self.box_ylo = box_dims[1][0]
        self.box_yhi = box_dims[1][1]
        self.box_zlo = box_dims[2][0]
        self.box_zhi = box_dims[2][1]
        self.molecules = molecules
        self.system_name = 'system.pdb' #system_name
        self.lines = []
        try:
            self.molfile = open('system.packmol', 'w')
        except:
            print 'Error opening file.'


    def _write_header(self):
        #TODO: Write comments here
        self.lines.append('tolerance 2.0' + '\n')
        self.lines.append('filetype pdb' + '\n')
        self.lines.append('output ' + self.system_name + '\n')

    def _write_molecule(self, mol_name, mol_number):
        self.lines.append('structure ' + mol_name + '.pdb' + '\n')
        self.lines.append('    number ' + str(mol_number) + '\n')
        self.lines.append('    inside box ' + str(self.box_xlo) + ' ' + str(self.box_ylo)  + ' ' + str(self.box_zlo) + ' ' +
                                            str(self.box_xhi) + ' ' + str(self.box_yhi)  + ' ' + str(self.box_zhi)  + '\n')

        self.lines.append('end structure ' + mol_name + '.pdb' + '\n')

    def build_system_file(self):
        self._write_header()
        for molecule in self.molecules:
            self.lines.append('\n')
            self._write_molecule(molecule[0].name, molecule[1])

    def save(self):
        try:
            self.molfile.writelines(self.lines)
        except:
            print "Error saving file"


class MTSystemWriter:
    def __init__(self, box_dims, molecules, system_name=''):
        self.box_xlo = box_dims[0][0]
        self.box_xhi = box_dims[0][1]
        self.box_ylo = box_dims[1][0]
        self.box_yhi = box_dims[1][1]
        self.box_zlo = box_dims[2][0]
        self.box_zhi = box_dims[2][1]
        self.molecules = molecules
        self.lines = []
        try:
            self.molfile = open('system.lt', 'w')
        except:
            print 'Error opening file.'



    def _write_header(self):
        for mol in self.molecules:
            self.lines.append('import ' + mol[0].name + '.lt' + '\n')

    def _write_molecules(self):
        m = 0
        for mol in self.molecules:
            self.lines.append('mol' + str(m) + ' = new ' + mol[0].name + '[%d]' % mol[1] + '\n')
            m += 1

    def _write_box(self):
        self.lines.append('write_once("Data Boundary") {' + '\n')
        self.lines.append('    ' + str(self.box_xlo) + ' ' + str(self.box_xhi) + ' xlo xhi' + '\n')
        self.lines.append('    ' + str(self.box_ylo) + ' ' + str(self.box_yhi) + ' ylo yhi' + '\n')
        self.lines.append('    ' + str(self.box_zlo) + ' ' + str(self.box_zhi) + ' zlo zhi' + '\n')
        self.lines.append('}' + '\n')


    def build_system_file(self):
        self._write_header()
        self.lines.append('\n')
        self._write_molecules()
        self.lines.append('\n')
        self._write_box()

    def save(self):
        try:
            self.molfile.writelines(self.lines)
        except:
            print "Error saving file"



class MTMolWriter:
    def __init__(self, potential, pymol_cmd):
        self.pymol_cmd = pymol_cmd
        self.mol_name = self.pymol_cmd.get_molecule_name()
        self.potential = potential
        self.molfile = None
        self.mol_model = None
        self.model_atom_types = None 
        self.lines = []
        self.atom_types = ATOM_TYPES[potential]
        try:
            self.molfile = open(self.mol_name + '.lt', 'w')
        except:
            print 'Error opening file.'

    def _write_header(self):
        self.lines.append('import ' + POTENTIALS[self.potential][1] + '\n')
        """ Do it later
        pot_atom_id = self.mol_model.resn
        for atom_type in self.model_atom_types:
            self.lines.append('# atom   ' + self.mol_model.resn + '  ' +
                              '"' + self.atom_types[pot_atom_id][1])
        """
        self.lines.append('\n')

    def _write_data_atoms(self):
        self.lines.append('  # atomID   molID  atomTyle  charge\
                          X        Y          Z\n')
        self.lines.append("  write('Data Atoms') {\n")
        for atom in self.mol_model.atom:
            atom_col = '    $atom:' + str(atom.index-1)
            mol_col = '$mol:.'
            atomid_col = '@atom:' + self.pymol_cmd._index_from_name(atom.name)
            charge_col = '0.0'
            x_col = str(atom.coord[0])
            y_col = str(atom.coord[1])
            z_col = str(atom.coord[2])
            row = '{0:<8} {1:<8} {2:<8} {3:<4} {4:<16} {5:<16} {6:<16} '\
                  .format(atom_col, mol_col, atomid_col,
                          charge_col, x_col, y_col, z_col)
            self.lines.append(row + '\n')
        self.lines.append('  }\n')
        self.lines.append('\n')

    def _write_data_bonds(self):
        self.lines.append("  write('Data Bond List') {\n")
        for bond in self.mol_model.bond:
            bond = bond.index
            bond_col = '    $bond:' + str(bond[0]) + str(bond[1])
            at1_col = '$atom:' + str(bond[0])
            at2_col = '$atom:' + str(bond[1])
            row = '{0:<12} {1:<12} {2:<12}'\
                  .format(bond_col, at1_col, at2_col)
            self.lines.append(row + '\n')
        self.lines.append('  }\n')
        self.lines.append('\n')

    def build_molecule_file(self):
    	self.mol_model = self.pymol_cmd.get_molecule_model()
        self.model_atom_types = get_model_atom_types(self.mol_model)
        self._write_header()
        self.lines.append(self.mol_name + ' inherits ' +
                          self.potential + '{\n')
        self._write_data_atoms()
        self._write_data_bonds()
        self.lines.append('} # ' + self.mol_name.title() + '\n')

    def save(self):
        try:
            self.molfile.writelines(self.lines)
        except:
            print "Error saving file"

if __name__ == '__main__':
    import pymolinterface
    pymol_cmd = pymolinterface.PymolInterface()
    pymol_cmd.load_molecule('octane.sdf')
    m = MTMolWriter('OPLSAA', pymol_cmd)
    m.build_molecule_file()
    m.save()
    #pymol.cmd.save("squalane.pdb")
    print get_OPLS_atom_types('LOPLSAA')
