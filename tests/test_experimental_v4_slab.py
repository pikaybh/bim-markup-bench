"""Original IFC Slab v0.4 native D0/negative tests; zero model calls."""
from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v4_projection import project_ifc_v4,_slab_mesh_bbox
from src.runtime.experimental_v4_slab import compile_declarative_xml_v4,SlabV4Error
from tools.oracle_bibimbap_slab_v04 import (
    IndependentSlabOracleError,verify_create,verify_update,verify_delete,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
SRC=BASE/"bibimbap-author-data"/"ifc"/"basic_tasks.ifc"
TOPO=BASE/"bibimbap-author-data"/"ifc"/"01"/"02"/"01_02_015.ifc"
NS="{urn:bim-markup-bench:toy:v0}"
GROUND_SLAB="35us3eQxb9WeuHdxm2wKYO"
UPPER_SLAB="11kJIqz$n2Jf_DfJV1SCVP"
TOPO_ABOVE="0CJwXarnHAeA7eFXxxI_is"
TOPO_BELOW="0CJwXarnHAeA7eFXxxI_hO"

def xml_slab(root,guid):
    return next(s for s in root.findall(".//"+NS+"Slab") if s.get("ifcGuid")==guid)

def state_bytes(tree):
    return etree.tostring(tree,encoding="utf8",xml_declaration=True)


@unittest.skipUnless(SRC.is_file(),"Pinned original IFC4X3 BIBIMBAP public basic file missing")
class OriginalSlabV4Tests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="bibi122-slab-")
        self.addCleanup(temp.cleanup)
        self.d=Path(temp.name)
        self.original=SRC
        self.original_sha=file_hash(self.original)
        self.addCleanup(lambda:self.assertEqual(file_hash(self.original),self.original_sha))
        model=ifcopenshell.open(str(self.original))
        self.native=self.d/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(model,"METER").write(str(self.native))
        self.native_sha=file_hash(self.native)
        self.addCleanup(lambda:self.assertEqual(file_hash(self.native),self.native_sha))
        self.projection=project_ifc_v4(self.native)

    def doc(self):
        return etree.fromstring(self.projection.xml)

    def test_projection_adds_two_original_opaque_slab_mesh_envelopes(self):
        self.assertEqual(dict(self.projection.supported_class_counts)["IfcSlab"],2)
        self.assertNotIn("IfcSlab",dict(self.projection.unsupported_class_counts))
        f=ifcopenshell.open(str(self.native))
        root=self.doc()
        slab_nodes=root.findall(".//"+NS+"Slab")
        self.assertEqual(len(slab_nodes),2)
        for row in slab_nodes:
            slab=f.by_guid(row.get("ifcGuid"))
            low,high=_slab_mesh_bbox(slab)
            actual=[float(row.get(k)) for k in ("x","y","z","width","depth","thickness")]
            expected=[*low,*(high[i]-low[i] for i in range(3))]
            for got,want in zip(actual,expected):
                self.assertAlmostEqual(got,want,places=6)

    def test_create_native_ifc_slab_and_independent_oracle(self):
        doc=self.doc()
        ground=next(x for x in doc.find(NS+"Levels") if float(x.get("elevation"))==0)
        etree.SubElement(doc.find(NS+"Elements"),NS+"Slab",{
            "id":"fixed_native_create_fixture",
            "level":ground.get("id"),
            "x":"-35","y":"-2.5","z":"0",
            "width":"10","depth":"5","thickness":"0.2",
        })
        dest=self.d/"created.ifc"
        res=compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertTrue(dest.exists())
        self.assertEqual(res.operations[0].operation,"CREATE_SLAB")
        self.assertFalse(res.as_dict()["original_45_case_native_backend_parity"])
        proof=verify_create(self.native,dest,res.operations[0].ifc_guid,
                            bounds_min=(-35,-2.5,0),bounds_max=(-25,2.5,0.2))
        self.assertEqual(proof["status"],"INDEPENDENT_NATIVE_SLAB_CREATE_PHYSICAL_IFC_VALIDATED")
        with self.assertRaises(IndependentSlabOracleError):
            verify_create(self.native,dest,res.operations[0].ifc_guid,
                          bounds_min=(-35,-2.5,0),bounds_max=(-26,2.5,0.2))

    def test_existing_real_slab_move_preserves_all_original_step(self):
        doc=self.doc()
        slab=xml_slab(doc,UPPER_SLAB)
        slab.set("z",str(float(slab.get("z"))-0.5))
        dest=self.d/"moved.ifc"
        res=compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertEqual(res.operations[0].operation,"MOVE_SLAB")
        proof=verify_update(self.native,dest,UPPER_SLAB,kind="move",delta=(0.,0.,-0.5))
        self.assertGreaterEqual(proof["original_root_preserved_count"],200)
        self.assertEqual(proof["verified_non_target_slab_count"],1)
        with self.assertRaises(IndependentSlabOracleError):
            verify_update(self.native,dest,UPPER_SLAB,kind="move",delta=(0.,0.,+0.5))

    def test_rectangle_reshape_preserves_min_and_other_slab(self):
        doc=self.doc()
        source=ifcopenshell.open(str(self.native))
        old_low,old_high=_slab_mesh_bbox(source.by_guid(GROUND_SLAB))
        slab=xml_slab(doc,GROUND_SLAB)
        slab.set("width",str(float(slab.get("width"))+2))
        slab.set("depth",str(float(slab.get("depth"))+1))
        dest=self.d/"reshaped.ifc"
        res=compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertEqual(res.operations[0].operation,"RESHAPE_SLAB_RECTANGLE")
        proof=verify_update(
            self.native,dest,GROUND_SLAB,kind="resize",
            new_bounds_min=old_low,
            new_bounds_max=(old_high[0]+2,old_high[1]+1,old_high[2]))
        self.assertIn("IfcRectangleProfileDef",proof["native_original_step_changed_types"])
        with self.assertRaises(IndependentSlabOracleError):
            verify_update(self.native,dest,GROUND_SLAB,kind="resize",
                          new_bounds_min=old_low,new_bounds_max=old_high)

    def test_delete_slab_preserves_original_other_product_and_material_type(self):
        doc=self.doc()
        slab=xml_slab(doc,GROUND_SLAB)
        slab.getparent().remove(slab)
        dest=self.d/"deleted.ifc"
        res=compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertEqual(res.operations[0].operation,"DELETE_SLAB")
        proof=verify_delete(self.native,dest,GROUND_SLAB)
        self.assertEqual(proof["preserved_unrelated_slab_meshes"],1)
        self.assertGreater(proof["preserved_surviving_original_products"],30)
        with self.assertRaises(IndependentSlabOracleError):
            verify_delete(self.native,dest,UPPER_SLAB)

    def test_existing_material_layer_slab_thickness_must_fail_closed(self):
        doc=self.doc()
        slab=xml_slab(doc,GROUND_SLAB)
        slab.set("thickness",str(float(slab.get("thickness"))+0.1))
        dest=self.d/"unsafe_thickness.ifc"
        with self.assertRaisesRegex(SlabV4Error,"linked shared material layers"):
            compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertFalse(dest.exists())

    def test_negative_geometry_bad_sizes(self):
        for field,value in (("width","0"),("depth","-5"),("thickness","0.001"),
                            ("width","200"),("x","10000000000000")):
            with self.subTest(field=field,value=value):
                doc=self.doc()
                slab=xml_slab(doc,GROUND_SLAB)
                slab.set(field,value)
                dst=self.d/("bad_"+field+"_"+value.replace("-","n")+".ifc")
                with self.assertRaises(Exception):
                    compile_declarative_xml_v4(self.native,state_bytes(doc),dst)
                self.assertFalse(dst.exists())

    def test_negative_original_source_hash_tamper_and_noop(self):
        doc=self.doc()
        d=self.d/"unchanged.ifc"
        with self.assertRaisesRegex(SlabV4Error,"Only a single isolated"):
            compile_declarative_xml_v4(self.native,state_bytes(doc),d)
        self.assertFalse(d.exists())
        doc.set("sourceModelSha256","0"*64)
        with self.assertRaises(Exception):
            compile_declarative_xml_v4(self.native,state_bytes(doc),d)
        self.assertFalse(d.exists())

    def test_negative_two_changed_slabs_rejected(self):
        doc=self.doc()
        xml_slab(doc,GROUND_SLAB).set("width","11.9")
        xml_slab(doc,UPPER_SLAB).set("z","2.5")
        dest=self.d/"two.ifc"
        with self.assertRaisesRegex(SlabV4Error,"Only a single isolated"):
            compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertFalse(dest.exists())

    def test_negative_add_a_slab_with_move_existing_rejected(self):
        doc=self.doc()
        ground=next(x for x in doc.find(NS+"Levels") if float(x.get("elevation"))==0)
        etree.SubElement(doc.find(NS+"Elements"),NS+"Slab",{
            "id":"new_multiple","level":ground.get("id"),
            "x":"15","y":"15","z":"0","width":"3","depth":"4","thickness":"0.25",
        })
        xml_slab(doc,GROUND_SLAB).set("y","20")
        dest=self.d/"mixed.ifc"
        with self.assertRaisesRegex(SlabV4Error,"Only a single isolated"):
            compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertFalse(dest.exists())

    def test_existing_output_refused_preserved(self):
        doc=self.doc()
        xml_slab(doc,GROUND_SLAB).set("x","2")
        dest=self.d/"existing.ifc"
        dest.write_bytes(b"NOT A MODEL")
        with self.assertRaisesRegex(SlabV4Error,"output path must be unused"):
            compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        self.assertEqual(dest.read_bytes(),b"NOT A MODEL")

    def test_independent_native_oracle_rejects_unrelated_ifc_product_change(self):
        doc=self.doc()
        xml_slab(doc,GROUND_SLAB).set("x","2")
        dest=self.d/"moved.ifc"
        compile_declarative_xml_v4(self.native,state_bytes(doc),dest)
        file=ifcopenshell.open(str(dest))
        file.by_guid(UPPER_SLAB).Name="INDEPENDENT NEGATIVE ALTERED OTHER SLAB"
        bad=self.d/"tampered.ifc"
        file.write(str(bad))
        with self.assertRaises(IndependentSlabOracleError):
            verify_update(self.native,bad,GROUND_SLAB,kind="move",
                          delta=(2.2,0,0))


@unittest.skipUnless(TOPO.is_file(),"Pinned original IFC topological_test_15 source absent")
class RealTopologicalSlabTests(unittest.TestCase):
    def test_native_two_slab_contact_only_target_moves_in_z(self):
        with tempfile.TemporaryDirectory(prefix="bibi122-topo15-") as temp:
            d=Path(temp)
            orig=ifcopenshell.open(str(TOPO))
            src=d/"input_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(orig,"METER").write(str(src))
            f=ifcopenshell.open(str(src))
            lower=_slab_mesh_bbox(f.by_guid(TOPO_BELOW))
            upper=_slab_mesh_bbox(f.by_guid(TOPO_ABOVE))
            required=lower[1][2]-upper[0][2]
            self.assertLess(required,0)
            root=etree.fromstring(project_ifc_v4(src).xml)
            current=xml_slab(root,TOPO_ABOVE)
            current.set("z",str(float(current.get("z"))+required))
            out=d/"contact.ifc"
            report=compile_declarative_xml_v4(src,state_bytes(root),out)
            self.assertEqual(report.operations[0].operation,"MOVE_SLAB")
            proof=verify_update(src,out,TOPO_ABOVE,kind="move",delta=(0,0,required))
            self.assertEqual(proof["verified_non_target_slab_count"],1)
            fnew=ifcopenshell.open(str(out))
            moved=_slab_mesh_bbox(fnew.by_guid(TOPO_ABOVE))
            unchanged=_slab_mesh_bbox(fnew.by_guid(TOPO_BELOW))
            self.assertAlmostEqual(moved[0][2],unchanged[1][2],places=5)


class UnlayeredSyntheticSlabTests(unittest.TestCase):
    def test_native_unlayered_slab_thickness_update_after_create(self):
        # The previous original slab linked to material layers, so thickness
        # update is forbidden there. Generate a standalone valid native Slab
        # first to demonstrate the *limited* supported operation.
        with tempfile.TemporaryDirectory(prefix="bibi122-unlayered-") as temp:
            d=Path(temp)
            src=Path(__file__).resolve().parents[1]/"tests"/"fixtures"/"synthetic"/"input.ifc"
            tree=etree.fromstring(project_ifc_v4(src).xml)
            lvl=next(x for x in tree.find(NS+"Levels") if float(x.get("elevation"))==0)
            etree.SubElement(tree.find(NS+"Elements"),NS+"Slab",{
                "id":"new_fixture_unlayered","level":lvl.get("id"),
                "x":"10","y":"10","z":"0",
                "width":"2","depth":"3","thickness":"0.2",
            })
            created=d/"slab_source.ifc"
            first=compile_declarative_xml_v4(src,state_bytes(tree),created)
            guid=first.operations[0].ifc_guid
            before=_slab_mesh_bbox(ifcopenshell.open(str(created)).by_guid(guid))
            changed=etree.fromstring(project_ifc_v4(created).xml)
            xml_slab(changed,guid).set("thickness","0.4")
            output=d/"thicker.ifc"
            second=compile_declarative_xml_v4(created,state_bytes(changed),output)
            self.assertEqual(second.operations[0].operation,"UPDATE_SLAB_THICKNESS")
            proof=verify_update(
                created,output,guid,kind="thickness",
                new_bounds_min=before[0],
                new_bounds_max=(before[1][0],before[1][1],before[1][2]+.2))
            self.assertEqual(proof["verified_non_target_slab_count"],1)


if __name__=="__main__":
    unittest.main()
