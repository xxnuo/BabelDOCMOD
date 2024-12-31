from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from yadt.parsers.miner.convert import TranslateConverter
from yadt.parsers.miner.interp import PDFPageInterpreterEx

class PDFMinerParser:
    def __init__(self, in_file):
        self.doc = PDFDocument(PDFParser(in_file))
        self.rsrcmgr = PDFResourceManager()
        self.device = TranslateConverter(self.rsrcmgr)
        self.ops_patch = {}
        self.interpreter = PDFPageInterpreterEx(self.rsrcmgr, self.device, self.ops_patch)
    
    def parse(self):
        for pageno, page in enumerate(PDFPage.create_pages(self.doc)):
            page.pageno = pageno
            self.interpreter.process_page(page)
            exit()


if __name__ == "__main__":
    in_file = open("test2.pdf", "rb")
    parser = PDFMinerParser(in_file)
    parser.parse()
    print(parser.ops_patch)