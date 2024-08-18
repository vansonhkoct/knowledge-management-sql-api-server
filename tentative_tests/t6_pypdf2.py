from PyPDF2 import PdfReader

reader = PdfReader("tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf")
for page in reader.pages:
    print(page.extract_text())

reader = PdfReader("tests/665b3dc2ac7044122d9b3d3a_EDBCM24090C.pdf")
for page in reader.pages:
    print(page.extract_text())
