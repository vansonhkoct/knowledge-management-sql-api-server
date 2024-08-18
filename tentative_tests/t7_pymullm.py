import pymupdf4llm
import pymupdf
import re


md_text = pymupdf4llm.to_markdown("tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf", page_chunks=True, write_images=False)
print(md_text)
# md_text = pymupdf4llm.to_markdown("tests/665b3dc2ac7044122d9b3d3a_EDBCM24090C.pdf", page_chunks=True)
# print(md_text)
# print()


# doc = pymupdf.Document("tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf")

# print(doc.page_count)
# print(doc.metadata)
# print(doc.get_toc())
# for index, page in enumerate(doc):
#   print(index, " - ", page, " - \n", page.get_text())



# doc = pymupdf.Document("tests/665b3dc2ac7044122d9b3d3a_EDBCM24090C.pdf")

# print(doc.page_count)
# print(doc.metadata)
# print(doc.get_toc())
# for index, page in enumerate(doc):
#   print(index, " - ", page, " - \n", page.get_text())

# doc = pymupdf.Document("tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf")
# for index, page in enumerate(doc):
#   print(index, " - ", page, " - \n")
#   md_text = pymupdf4llm.to_markdown("tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf", pages=[index])
#   md_text = re.sub(r'\*\*', '', md_text)
#   print(md_text)

doc = pymupdf.Document("tests/665b3dc2ac7044122d9b3d3a_EDBCM24090C.pdf")
for index, page in enumerate(doc):
  print("===================\n", index, " - ", page, " - \n")
  md_text = pymupdf4llm.to_markdown("tests/665b3dc2ac7044122d9b3d3a_EDBCM24090C.pdf", pages=[index])
  md_text = re.sub(r'\*\*', '', md_text)
  print(md_text)


# md_text = pymupdf4llm.to_markdown(doc[0])
# print(md_text)
