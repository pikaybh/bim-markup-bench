"""Safe, source-preserving typed parser for toy declarative BIM markup v0.1.

This parser does NOT edit any IFC model or call any LLM. Every parse first
enforces byte quotas/DTD rejection, then validates against a pinned local XSD,
then constructs immutable typed AST nodes and byte-accurate XML start spans.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import re
from pathlib import Path
from xml.parsers import expat

from lxml import etree

from src.runtime.ast import BuildingDocument, ElementNode, SourceSpan
from src.runtime.markup_normal_form import canonical_semantic_xml, DECIMAL_ATTRS, NS
from src.security.agent_boundary import check_xml_bytes, SecurityBoundaryError

ROOT = Path(__file__).resolve().parents[2]
XSD_PATH = ROOT / "spec/toy_markup_v0.xsd"
MAX_DEPTH = 96
MAX_ELEMENTS = 4096
MAX_ATTRIBUTES = 32
MAX_START_TAG_BYTES = 16_384


class MarkupParseError(ValueError):
    def __init__(self, diagnostic: dict):
        self.diagnostic = diagnostic
        super().__init__(diagnostic["code"] + ": " + diagnostic["message"])

def safe_diagnostic(code: str, message: str, file: str,
                    line: int = 1, column: int = 1, element_id: str | None = None) -> dict:
    # Neither source XML nor arbitrary external paths can become a diagnostic.
    file = Path(file).name or "building.xml"
    if file.startswith(".") or re.search(r"sk-[A-Za-z0-9_-]{10,}", file):
        file = "building.xml"
    message = re.sub(r"sk-[A-Za-z0-9_-]{10,}", "[REDACTED]", message)
    message = re.sub(r"OPENAI_API_KEY\s*=\s*[^\s]+", "OPENAI_API_KEY=[REDACTED]", message)
    if element_id is not None and (
        len(element_id) > 128
        or not re.fullmatch(r"[A-Za-z_][\w.\-]*", element_id)
        or re.search(r"sk-[A-Za-z0-9_-]{10,}", element_id)
    ):
        element_id = None
    return {
        "code": str(code),
        "severity": "ERROR",
        "message": message[:240] if message else "Invalid XML document",
        "file": file,
        "line": max(1,int(line)),
        "column": max(1,int(column)),
        "element_id": element_id,
    }

def _schema() -> etree.XMLSchema:
    # Schema source is trusted and local. No network, DTD or external entities.
    parser = etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,huge_tree=False)
    root = etree.parse(str(XSD_PATH), parser=parser)
    if root.find(".//{http://www.w3.org/2001/XMLSchema}include") is not None:
        raise RuntimeError("Schema includes are forbidden")
    if root.find(".//{http://www.w3.org/2001/XMLSchema}import") is not None:
        raise RuntimeError("Schema imports are forbidden")
    return etree.XMLSchema(root)

def _find_attr_col(lines: list[bytes], line: int, msg: str) -> int:
    if not (1 <= line <= len(lines)):
        return 1
    text=lines[line-1].decode("utf-8",errors="replace")
    patterns = re.findall(r"attribute ['\"]([^'\"]+)['\"]",msg)
    for attr in patterns:
        idx=text.find(attr+"=")
        if idx >= 0:
            return idx+1
    first = text.find("<")
    return first+1 if first>=0 else 1

def _start_tag_end(data: bytes, start: int) -> int:
    # Scan opening tag only, respecting quoted '>' characters. This is used for
    # source mapping, not tokenizing, so must not execute XML entities or fetch.
    q = None
    end=min(len(data),start+MAX_START_TAG_BYTES)
    for i in range(start,end):
        c=data[i]
        if q is None:
            if c in (ord('"'),ord("'")): q=c
            elif c==ord(">"): return i+1
        elif c==q:
            q=None
    raise ValueError("XML start tag exceeds permitted length or is incomplete")

def _expat_spans(data: bytes, source_filename: str) -> list[tuple[str,SourceSpan]]:
    parser=expat.ParserCreate(namespace_separator="}")
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.ExternalEntityRefHandler=lambda *_: 0
    parser.StartDoctypeDeclHandler=lambda *_: (_ for _ in ()).throw(ValueError("DTD forbidden"))
    positions=[]
    depth=0
    def start(name,attrs):
        nonlocal depth
        depth += 1
        if depth>MAX_DEPTH:
            raise ValueError("XML nesting depth exceeded")
        if len(positions)>=MAX_ELEMENTS:
            raise ValueError("XML element count exceeded")
        if len(attrs)>MAX_ATTRIBUTES:
            raise ValueError("Too many XML attributes")
        offset=parser.CurrentByteIndex
        last_newline=data.rfind(b"\n", 0, offset)
        # Expat reports byte columns. Expose character columns to human editors;
        # keep byte offsets separately for exact source slices.
        character_column=len(data[last_newline+1:offset].decode("utf-8"))+1
        positions.append((name,SourceSpan(
            file=source_filename,line=parser.CurrentLineNumber,
            column=character_column,
            start_byte=offset,start_tag_end_byte=_start_tag_end(data,offset),
        )))
    def end(_):
        nonlocal depth
        depth -= 1
    parser.StartElementHandler=start
    parser.EndElementHandler=end
    parser.Parse(data,True)
    return positions

def _parse_element(element: etree._Element, span: SourceSpan, role: str) -> ElementNode:
    attrs = tuple(sorted((str(k),str(v)) for k,v in element.attrib.items()))
    typed=[]
    for key,value in attrs:
        if key in DECIMAL_ATTRS:
            try:
                n=Decimal(value)
            except InvalidOperation as exc:
                raise ValueError("Invalid decimal in XML attribute "+key) from exc
            if not n.is_finite():
                raise ValueError("Nonfinite decimal in XML attribute "+key)
            typed.append((key,n))
        else:
            typed.append((key,value))
    return ElementNode(
        kind=etree.QName(element).localname,id=element.get("id"),
        ifc_guid=element.get("ifcGuid"),raw_attributes=attrs,
        typed_attributes=tuple(typed),span=span,role=role,
    )

def parse_xml(data: bytes, *, filename: str="building.xml",
              expected_source_sha256: str | None = None) -> BuildingDocument:
    """Parse XML bytes; no side effects; all error paths fail closed."""
    filename = Path(filename).name or "building.xml"
    try:
        check_xml_bytes(data)
        positions = _expat_spans(data, filename)
    except (SecurityBoundaryError,ValueError,expat.ExpatError,TypeError) as exc:
        raise MarkupParseError(safe_diagnostic("XML_SECURITY_OR_SYNTAX",type(exc).__name__+": "+str(exc),filename,
            getattr(exc,"lineno",1),getattr(exc,"offset",1))) from exc

    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,
                           huge_tree=False,remove_comments=False)
    try:
        document=etree.fromstring(data,parser=parser)
    except etree.XMLSyntaxError as exc:
        raise MarkupParseError(safe_diagnostic("XML_MALFORMED",str(exc).split(", line")[0],
                    filename,exc.lineno or 1,exc.offset or 1)) from exc
    if document.tag != "{"+NS+"}Building":
        raise MarkupParseError(safe_diagnostic("XML_WRONG_ROOT","Unexpected namespace or root element",filename))
    lines=data.splitlines()
    try:
        schema = _schema()
    except (OSError,etree.XMLSchemaParseError) as exc:
        # Fatal internal runtime setup: not user source error.
        raise RuntimeError("Pinned local XSD schema could not be loaded") from exc
    if not schema.validate(document):
        issue=schema.error_log.last_error
        message=str(issue.message) if issue is not None else "XML does not satisfy the pinned schema"
        line=issue.line if issue is not None else 1
        # Best-effort identify the offending element without dumping source
        # text or leaking grader/model paths into diagnostics.
        bad_nodes=[e for e in document.iter()
                   if isinstance(e.tag,str) and e.sourceline==line and e.get("id")]
        element_id=bad_nodes[-1].get("id") if bad_nodes else None
        raise MarkupParseError(safe_diagnostic("XML_SCHEMA",message,filename,line,
                            _find_attr_col(lines,line,message),element_id))

    # lxml preserves comments and other node types that expat does not count as
    # start elements. Filter them; compare qnames to avoid hidden mapping errors.
    elements=[e for e in document.iter() if isinstance(e.tag,str)]
    if len(positions) != len(elements):
        raise MarkupParseError(safe_diagnostic("XML_SOURCEMAP","Parser node positions inconsistent",filename))
    positions_by_object={}
    for node,(name,span) in zip(elements,positions):
        if node.tag.replace("{","")!=name:
            raise MarkupParseError(safe_diagnostic("XML_SOURCEMAP","Source XML and AST nodes differ",filename,span.line,span.column))
        positions_by_object[id(node)]=span

    root_span=positions_by_object[id(document)]
    source_hash=document.get("sourceModelSha256")
    if not source_hash:
        raise MarkupParseError(safe_diagnostic("XML_SOURCE_HASH","Missing immutable IFC hash",filename))
    if expected_source_sha256 is not None and source_hash != expected_source_sha256:
        raise MarkupParseError(safe_diagnostic("XML_SOURCE_HASH","Immutable input IFC content hash mismatch",filename,
                            root_span.line,root_span.column))
    sections={etree.QName(el).localname:el for el in document if isinstance(el.tag,str)}
    def nodes(section,role):
        parent=sections.get(section)
        if parent is None:return ()
        return tuple(_parse_element(el,positions_by_object[id(el)],role)
                     for el in parent if isinstance(el.tag,str))
    try:
        digest=hashlib.sha256(canonical_semantic_xml(data)).hexdigest()
        return BuildingDocument(
            source_filename=filename,source_bytes=data,
            source_byte_sha256=hashlib.sha256(data).hexdigest(),
            semantic_sha256=digest,
            source_model_sha256=source_hash,
            namespace=NS,units=document.get("units",""),
            ifc_schema=document.get("ifcSchema",""),
            levels=nodes("Levels","level"),
            elements=nodes("Elements","element"),
            relations=nodes("Relations","relation"),
            root_span=root_span,
        )
    except (ValueError,SecurityBoundaryError) as exc:
        raise MarkupParseError(safe_diagnostic("XML_AST",str(exc),filename)) from exc

@dataclass(frozen=True)
class ParseOutcome:
    committed: BuildingDocument
    accepted: bool
    diagnostics: tuple[dict,...]

def try_parse_update(previous: BuildingDocument, source: bytes) -> ParseOutcome:
    """Keep the exact last valid document if user/LLM saves half-written XML."""
    try:
        current=parse_xml(source,filename=previous.source_filename,
                          expected_source_sha256=previous.source_model_sha256)
        return ParseOutcome(committed=current,accepted=True,diagnostics=())
    except MarkupParseError as exc:
        return ParseOutcome(committed=previous,accepted=False,
                            diagnostics=(exc.diagnostic,))
