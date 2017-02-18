import urllib2
import urllib
import pubchempy as pcp
import json
import os
import Image
import imageconvert
from itertools import chain


#class MoleculeFetcher(threading.Thread):
class MoleculeFetcher():

    def __init__(self):
        self.PUBCHEM_URL = 'https://pubchem.ncbi.nlm.nih.gov/pcautocp/pcautocp.cgi'
        self.THUMBNAIL_SIZE = 200 

    def search_molecules(self, mol_substr, no_mols=20):
        values = {'dict': 'pc_compoundnames', 'q': mol_substr, 'n': no_mols}
        print values
        data = urllib.urlencode(values)
        response = urllib2.urlopen(urllib2.Request(self.PUBCHEM_URL, data))
        response = response.read()
        mol_data = json.loads(response)

        def a():
            print self.PUBCHEM_URL

        return mol_data['autocp_array']

    def get_mol_data(self, molecule):
        data = pcp.get_properties('MolecularWeight,MolecularFormula,IUPACName',
                                  molecule, namespace='name',
                                  name_type='complete')

        return data[0]

    def _clean_tags(self, tags):
        return [s.lower().rstrip('s') for t in tags for s in t.split(" ") if s not in [" ", ""]]

    def get_mol_tags(self, mol_name):
        hex = None
	tags = []
        try:
            hex = pcp.request(mol_name, namespace='name', domain='compound', operation='classification', output='JSON', name_type='complete')
        except:
            print "Tags cannot be fetched for " + mol_name
            return tags
        text = json.loads(hex.read())
        l1 = len(text["Hierarchies"]["Hierarchy"])
        for i in xrange(2):
            try:
                l2 = len(text["Hierarchies"]["Hierarchy"][i]["Node"])
            except:
                pass
            for j in xrange(l2):
                try:
                    tags.append(text["Hierarchies"]["Hierarchy"][i]["Node"][j]["Information"]["Name"])
                except:
                    pass
        return self._clean_tags(tags)

    def _get_mol_image(self, mol_name, path='.', image_size=200):
        file_path = os.path.join(path, mol_name + '.png')
        image_size_str = str(image_size) + "x" + str(image_size)
        try:
            os.remove(mol_name+'.png')
        except:
            pass
        pcp.download('PNG', file_path, mol_name, 'name', image_size=image_size_str)
	
    def get_mol_SDF(self, mol_name, path='.'): 
        file_path = os.path.join(path, mol_name + '.sdf')
        pcp.download('SDF', file_path, mol_name, 'name', overwrite=True)


    def get_mol_thumbnail(self, mol_name):
        SIZE = self.THUMBNAIL_SIZE
        SIZE_MOL = int(self.THUMBNAIL_SIZE/3.0)
        self._get_mol_image(mol_name)
        im = Image.open(mol_name + ".png")
        bbox = im.getbbox()
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        print w, h
        if (w <= SIZE/3.0 and h <= SIZE/3.0):
            print "ENTRO"
            resize_dim = int(SIZE/float(max(w, h))*SIZE_MOL)
            os.remove(mol_name+".png")
            print resize_dim
            self._get_mol_image(mol_name, image_size=resize_dim)
            im = Image.open(mol_name+".png")
            bbox = im.getbbox()
            extra_pix_w = bbox[2] - bbox[0] - SIZE
            extra_pix_h = bbox[3] - bbox[1] - SIZE
            bbox = list(bbox)
            bbox[0] += extra_pix_w / 2
            bbox[2] -= extra_pix_w / 2 + extra_pix_w % 2
            bbox[1] += extra_pix_h / 2
            bbox[3] -= extra_pix_h / 2 + extra_pix_h % 2
            im = im.crop(bbox)
            im.save("test2.png")
        return imageconvert.WxImageFromPilImage(im)




#molfetch = MoleculeFetcher()
#molfetch.get_mol_tags("decane")
#molfetch.get_mol_thumbnail("decane")

#molecules = molfetch.search_molecules('me', 5)
"""
for mol_name in molecules:
    molecule_data = molfetch.get_mol_data(mol_name)
    fetched_name = molecule_data['IUPACName']
    if fetched_name != mol_name:
        print "Name inconsistency: ", fetched_name, " : ", mol_name
    print molecule_data
    """


