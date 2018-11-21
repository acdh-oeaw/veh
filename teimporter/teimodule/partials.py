gen_tei_header = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
      <fileDesc>
         <titleStmt>
            <title/>
         </titleStmt>
         <publicationStmt>
            <p/>
         </publicationStmt>
         <sourceDesc>
            <p/>
         </sourceDesc>
      </fileDesc>
  </teiHeader>
  <text>
      <body/>
  </text>
</TEI>
"""


person_tei_dict = {
    'name': "{http://www.tei-c.org/ns/1.0}surname",
    'first_name': "{http://www.tei-c.org/ns/1.0}forename",
    'start_date': "{http://www.tei-c.org/ns/1.0}birth",
    'end_date': "{http://www.tei-c.org/ns/1.0}death",
}
