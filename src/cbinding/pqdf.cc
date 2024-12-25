#include <pybind11/pybind11.h>
#include <qpdf/QPDFJob.hh>
#include <stdexcept>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)


int convert_pdf_to_json(char* input_file, char* output_file) {
    try {
        QPDFJob job;
        job.config()
            ->inputFile(input_file)
            ->jsonOutput("latest")
            ->outputFile(output_file);

        job.run();
        return 0;
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("PDF conversion failed: ") + e.what());
    }
}

int convert_json_to_pdf(char* input_file, char* output_file) {
    try {
        QPDFJob job;
        job.config()
            ->inputFile(input_file)
            ->jsonInput()
            ->outputFile(output_file);

        job.run();
        return 0;
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("JSON conversion failed: ") + e.what());
    }
}


namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
    m.def("convert_pdf_to_json", &convert_pdf_to_json, 
        py::arg("input_file"),
        py::arg("output_file"),
        R"pbdoc(
        Convert a PDF to a JSON object

        Args:
            input_file (str): Path to the input PDF file
            output_file (str): Path where the output JSON will be saved

        Returns:
            int: 0 on success

        Raises:
            RuntimeError: If PDF conversion fails
        )pbdoc");
    m.def("convert_json_to_pdf", &convert_json_to_pdf, 
        py::arg("input_file"),
        py::arg("output_file"),
        R"pbdoc(
        Convert a JSON object to a PDF

        Args:
            input_file (str): Path to the input JSON file
            output_file (str): Path where the output PDF will be saved

        Returns:
            int: 0 on success
        )pbdoc");   
#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}