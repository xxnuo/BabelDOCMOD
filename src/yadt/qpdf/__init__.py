import tempfile
import yadt._core as core

def file_convert_pdf_to_json(input_file, output_file):
    return core.convert_pdf_to_json(input_file, output_file)


def file_convert_json_to_pdf(input_file, output_file):
    return core.convert_json_to_pdf(input_file, output_file)

    
def convert_pdf_to_json(pdf_data: bytes) -> bytes:
    pdf_file = tempfile.mktemp()
    with open(pdf_file, "wb") as f:
        f.write(pdf_data)
    json_file = tempfile.mktemp()
    file_convert_pdf_to_json(pdf_file, json_file)
    with open(json_file, "rb") as f:
        return f.read()

def convert_json_to_pdf(json_data: bytes) -> bytes:
    json_file = tempfile.mktemp()
    with open(json_file, "wb") as f:
        f.write(json_data)
    pdf_file = tempfile.mktemp()
    file_convert_json_to_pdf(json_file, pdf_file)
    with open(pdf_file, "rb") as f:
        return f.read()