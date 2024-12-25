import yadt.qpdf as qpdf
import json
import xml.etree.ElementTree as ET

def parse_pdf(pdf_data: bytes) -> bytes:
    # Convert PDF to JSON using qpdf
    json_data = qpdf.convert_pdf_to_json(pdf_data)
    json_obj = json.loads(json_data)
    
    # Create root document element
    ns = {"wp": "urn:ns:yadt:dpml"}
    ET.register_namespace('wp', ns['wp'])
    root = ET.Element(f"{{{ns['wp']}}}document")
    
    # Add document properties
    doc_props = ET.SubElement(root, f"{{{ns['wp']}}}document-properties")
    
    # Process metadata object
    metadata_pdf_obj = ET.SubElement(root, f"{{{ns['wp']}}}pdfobject")
    metadata_pdf_obj.set('type', 'metadata')
    add_json_as_key_value_pairs(metadata_pdf_obj, json_obj['qpdf'][0])
    
    # Process PDF objects
    for key, value in json_obj['qpdf'][1].items():
        if key.startswith('obj:'):
            pdf_obj = ET.SubElement(root, f"{{{ns['wp']}}}pdfobject")
            key = key.replace('obj:', '')
            obj_num, gen_num = key.split()[0:2]
            pdf_obj.set('objectNumber', obj_num)
            pdf_obj.set('generationNumber', gen_num)
            pdf_obj.set('type', 'obj')
            add_json_as_key_value_pairs(pdf_obj, value)
        if key.startswith('trailer'):
            pdf_obj = ET.SubElement(root, f"{{{ns['wp']}}}pdfobject")
            pdf_obj.set('type', 'trailer')
            add_json_as_key_value_pairs(pdf_obj, value)
    
    # Convert to XML bytes
    return ET.tostring(root, encoding='UTF-8', xml_declaration=True)

def add_json_as_key_value_pairs(parent_element, json_data):
    """Recursively convert JSON data to keyValuePair elements"""
    ns = {"wp": "urn:ns:yadt:dpml"}
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            kvp = ET.SubElement(parent_element, f"{{{ns['wp']}}}keyValuePair")
            kvp.set('key', str(key))
            if isinstance(value, (str, int, float, bool)) or value is None:
                kvp.set('value', str(value))
            elif isinstance(value, (dict, list)):
                add_json_as_key_value_pairs(kvp, value)
    
    elif isinstance(json_data, list):
        for item in json_data:
            array_item = ET.SubElement(parent_element, f"{{{ns['wp']}}}arrayItem")
            if isinstance(item, (str, int, float, bool)) or item is None:
                array_item.set('value', str(item))
            else:
                add_json_as_key_value_pairs(array_item, item)
    
if __name__ == "__main__":
    with open("demo.pdf", "rb") as f:
        pdf_data = f.read()
    result = parse_pdf(pdf_data)
    with open("demo.xml", "wb") as f:
        f.write(result)
