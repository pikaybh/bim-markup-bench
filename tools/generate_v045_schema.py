"""Generate v0.45 schema from pinned v0.44 source read-only schema."""
from pathlib import Path
from lxml import etree

root=Path(__file__).resolve().parents[1]
source=root/"spec"/"original_native_step_readonly_v044.xsd"
destination=root/"spec"/"original_native_typed_mutations_v045.xsd"
text=source.read_text(encoding="utf8")
old="""     </xs:complexType>
    </xs:element>
   </xs:sequence>
   <xs:attribute name="version" type="xs:string" use="required"/>"""
replacement="""     </xs:complexType>
    </xs:element>
    <xs:element name="NativeEditPlan">
     <xs:complexType>
      <xs:choice minOccurs="0" maxOccurs="1">
       <xs:element name="SetSlabRectangleDimensions">
        <xs:complexType>
         <xs:attribute name="ifcGuid" type="b:IfcGuid" use="required"/>
         <xs:attribute name="newXDimM" type="xs:decimal" use="required"/>
         <xs:attribute name="newYDimM" type="xs:decimal" use="required"/>
        </xs:complexType>
       </xs:element>
       <xs:element name="MoveColumnPlacement">
        <xs:complexType>
         <xs:attribute name="ifcGuid" type="b:IfcGuid" use="required"/>
         <xs:attribute name="newWorldOriginXM" type="xs:decimal" use="required"/>
         <xs:attribute name="newWorldOriginYM" type="xs:decimal" use="required"/>
        </xs:complexType>
       </xs:element>
       <xs:element name="SetAllMappedColumnDepth">
        <xs:complexType>
         <xs:attribute name="newDepthM" type="xs:decimal" use="required"/>
        </xs:complexType>
       </xs:element>
       <xs:element name="DeleteColumnsByGuid">
        <xs:complexType>
         <xs:sequence>
          <xs:element name="DeleteColumn" minOccurs="1" maxOccurs="9">
           <xs:complexType>
            <xs:attribute name="ifcGuid" type="b:IfcGuid" use="required"/>
           </xs:complexType>
          </xs:element>
         </xs:sequence>
        </xs:complexType>
       </xs:element>
      </xs:choice>
      <xs:attribute name="planVersion" type="xs:string" use="required" fixed="0.45"/>
      <xs:attribute name="sourceOriginalIFCSha256" type="b:Sha256" use="required"/>
      <xs:attribute name="editAuthority" type="xs:string" use="required" fixed="SINGLE_TYPED_PLAN_NATIVE_MUTATION"/>
     </xs:complexType>
    </xs:element>
   </xs:sequence>
   <xs:attribute name="version" type="xs:string" use="required"/>"""
assert text.count(old)==1
text=text.replace(old,replacement)
old_attr='   <xs:attribute name="nativeMutationPermission" type="b:Readonly" use="required"/>'
assert text.count(old_attr)==2
prefix,suffix=text.rsplit(old_attr,1)
text=prefix+'   <xs:attribute name="nativeMutationPermission" type="xs:string" use="required"/>'+suffix
etree.XMLSchema(etree.fromstring(text.encode("utf8")))
with destination.open("xb") as file:
    file.write(text.encode("utf8"))
print("V045_VALID_SOURCE_DERIVED_XSD",destination,len(text))
