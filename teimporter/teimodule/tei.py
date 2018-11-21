import lxml.etree as ET
import hashlib


tei_document = """
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


class TeiReader():

    """ a class to read an process tei-documents"""

    def __init__(self, xml):
        self.ns_tei = {'tei': "http://www.tei-c.org/ns/1.0"}
        self.ns_xml = {'xml': "http://www.w3.org/XML/1998/namespace"}
        self.nsmap = {
            'tei': "http://www.tei-c.org/ns/1.0",
            'xml': "http://www.w3.org/XML/1998/namespace",
            'tcf': "http://www.dspin.de/data/textcorpus"
        }
        self.file = xml
        try:
            self.original = ET.parse(self.file)
        except:
            self.original = ET.fromstring(self.file)
        try:
            self.tree = ET.parse(self.file)
        except:
            self.tree = ET.fromstring(self.file)
        try:
            self.parsed_file = ET.tostring(self.tree, encoding="utf-8")
        except:
            self.parsed_file = "parsing didn't work"

    def create_place(self, xml_id="something", text="someplace", lat=None, lng=None, ref_id=None):

        """ creates a tei:place element with an @xml:id
        and a child element tei:placeName"""

        place = ET.Element("{http://www.tei-c.org/ns/1.0}place")
        place.attrib['{http://www.w3.org/XML/1998/namespace}id'] = xml_id
        placeName = ET.Element("{http://www.tei-c.org/ns/1.0}placeName",)
        placeName.text = text
        place.append(placeName)
        location = ET.Element("{http://www.tei-c.org/ns/1.0}location")
        geo = ET.Element("{http://www.tei-c.org/ns/1.0}geo")
        geo.attrib['decls'] = '#LatLng'
        geo.text = "{} {}".format(lat, lng)
        location.append(geo)
        place.append(location)
        if isinstance(ref_id, str):
            idno = ET.Element("{http://www.tei-c.org/ns/1.0}idno")
            idno.text = ref_id
            place.append(idno)
        elif isinstance(ref_id, list):
            for x in ref_id:
                idno = ET.Element("{http://www.tei-c.org/ns/1.0}idno")
                idno.text = x
                place.append(idno)
        return place

    def get_places_elements(self, ids):

        """ takes a list of elements with a text node
        and a @ref attribute and returns a tei:place elements
        * with an xml:id,
        * and a placeName child element"""

        places = []
        for x in ids:
            text = x['text']
            ref = x['ref'][1:]
            place = (text, ref)
            places.append(place)
        place_elements = []
        for text, ref in set(places):
            place = self.create_place(ref, text)
            place_elements.append(place)
        return place_elements

    def find_elements(self, tei_element='placeName'):

        """ parses a tei:TEI//tei:text element,
        * extracts all nodes matching tei_element,
        * and reaturns a dictionary containing
        ** the name of the searched element: 'tei_element',
        ** the number of hits: 'nr_of_hits',
        ** and a list of the found element (as lxml element objects)
        """

        result = {'tei_element': tei_element}
        result['hits'] = self.tree.xpath(
            '//tei:text//tei:{}'.format(tei_element), namespaces=self.ns_tei
        )
        result['nr_of_hits'] = len(result['hits'])
        return result

    def add_ids(self, tei_element='placeName', id_prefix='place'):

        """ reads an tei-xml document
        * looks for tei_elements,
        * adds generic @ref (hashed text-node),
        * and returns a tuple containing
        ** a list of elements,
        ** and the updated xml-tree object.
        """

        hits = self.find_elements(tei_element)['hits']
        ids = []
        for x in hits:
            if x.text is None:
                break
            try:
                x.attrib['ref']
                ids.append({'text': x.text, 'ref': x.attrib['ref'], 'node': x})
            except:
                ref = hashlib.md5(x.text.encode('utf-8')).hexdigest()
                x.attrib['ref'] = "#{}_{}".format(id_prefix, ref)
                ids.append({'text': x.text, 'ref': x.attrib['ref'], 'node': x})
        return ids, self.tree

    def create_place_index(self, nodes):

        """ takes a list of elements and transforms them into an place index-file"""

        places = self.get_places_elements(nodes)
        list_place = ET.Element("{http://www.tei-c.org/ns/1.0}listPlace")
        for x in places:
            list_place.append(x)
        new_doc = ET.fromstring(tei_document)
        body = new_doc.xpath('//tei:body', namespaces=self.ns_tei)[0]
        body.append(list_place)
        return new_doc

    def create_place_index_from_place_elements(self, nodes):

        """ takes a list of elements and transforms them into an place index-file"""

        places = nodes
        list_place = ET.Element("{http://www.tei-c.org/ns/1.0}listPlace")
        for x in places:
            list_place.append(x)
        new_doc = ET.fromstring(tei_document)
        body = new_doc.xpath('//tei:body', namespaces=self.ns_tei)[0]
        body.append(list_place)
        return new_doc

    def export_tei(self, tei_doc, export_file='teihencer_export.xml'):

        """ writes any xml node to a file """

        file = export_file
        with open(file, 'wb') as f:
            f.write(ET.tostring(tei_doc, pretty_print=True, encoding="UTF-8"))
        return "file stored as {}".format(file)

    def xml_to_str(self):
        return ET.tostring(self.tree, encoding='unicode', method='xml')


class TeiPlaceList(TeiReader):

    def parse_placelist(self):

        """ parses an XML/TEI document and returns
        * a dict with
        ** a list of all //tei:listPlace//tei:place elements
        ** and the length of this list
        """
        places = self.tree.xpath('//tei:listPlace//tei:place', namespaces=self.ns_tei)
        return {"amount": len(places), "places": places}

    def parse_placelist_from_lxml_node(self, placelist):

        """ parses an lxml element node
        * a dict with
        ** a list of all //tei:listPlace//tei:place elements
        ** and the length of this list
        """
        places = placelist.xpath('//tei:listPlace//tei:place', namespaces=self.ns_tei)
        return {"amount": len(places), "places": places}

    # def placeAndID(self, placeelement, xpath)

    def place2dict(self, placeelement):

        """parses place element object and returns
        * a python dict with
        ** child elements,
        ** their attributes,
        ** and the element object
        """

        place = {'xml:id': placeelement.xpath('./@xml:id', namespaces=self.ns_xml)}
        place['type'] = placeelement.xpath('./type')
        place['placeNames'] = []
        place['idno'] = []
        for x in placeelement.xpath('.//tei:placeName', namespaces=self.ns_tei):
            place_name = {}
            place_name['text'] = " ".join((x.xpath('.//text()')))
            place_name['type'] = x.xpath('./@type')
            place_name['key'] = x.xpath('./@key')
            place_name['ref'] = x.xpath('./@ref')
            place_name['lang'] = x.xpath('./@xml:lang', namespaces=self.ns_xml)
            place['placeNames'].append(place_name)
        for x in placeelement.xpath('.//tei:idno', namespaces=self.ns_tei):
            idno = {}
            idno['text'] = " ".join((x.xpath('.//text()')))
            idno['type'] = x.xpath('./@type')
            place['idno'].append(idno)
        geo = {}
        try:
            geo['coordinates'] = placeelement.xpath(
                './/tei:geo/text()',
                namespaces=self.ns_tei)[0].split(" ")
            geo['type'] = placeelement.xpath('.//tei:geo/@decls', namespaces=self.ns_tei)
        except:
            geo['coordinates'] = None
            geo['type'] = None
        place['geo'] = geo
        place['node'] = placeelement
        place['urls'] = []
        for x in placeelement.xpath('.//tei:ptr', namespaces=self.ns_tei):
            place['urls'].append(x.xpath('./@target'))
        return place

    def fetch_ID(self, element, xpath2ID, ndtype=None):

        """takes a place node, a xpath pointing to a norm data ID/LINK,
        and optional a normdata type and returns
        * a dict with
        ** the passed in params,
        ** the fetched normdata ID (as URL!),
        ** and a "status" bool indicating if the xpath hit something (True) or not (False)
        """
        namespaces = {
            'tei': "http://www.tei-c.org/ns/1.0",
            'xml': "http://www.w3.org/XML/1998/namespace",
            'geonames': 'http://www.geonames.org/',
            'gnd': 'http://d-nb.info/gnd/'
        }
        result = {
            'xpath': xpath2ID,
            'fetched_id': None,
            'element': element,
        }
        try:
            fetched_id = element.xpath(xpath2ID, namespaces=namespaces)[0]
            fetched_id = fetched_id.strip()
        except:
            result['status'] = False
            return result
        if ndtype:
            if fetched_id.startswith(namespaces[ndtype]):
                pass
            if fetched_id.startswith('http'):
                pass
            else:
                fetched_id = namespaces[ndtype]+fetched_id+'/'
                fetched_id
        else:
            pass
        result['fetched_id'] = fetched_id
        result['status'] = True
        return result


class TeiPersonList(TeiReader):

    def parse_listperson(self, gnd=False):

        """ parses an XML/TEI document and returns
        * a dict with
        ** a list of all //tei:listPerson//tei:person elements
        ** and the length of this list
        """
        if gnd:
            items = self.tree.xpath(
                '//tei:listPerson//tei:person[.//tei:idno[@type="GND"]]',
                namespaces=self.ns_tei
            )
        else:
            items = self.tree.xpath('//tei:listPerson//tei:person', namespaces=self.ns_tei)
        return {"amount": len(items), "persons": items}

    def person2dict(self, personelement):

        """parses an tei:person node and returns a python person like data dict """

        person = {}
        person['node'] = personelement
        try:
            person['xml_id'] = personelement.xpath('./@xml:id', namespaces=self.ns_xml)[0]
        except IndexError:
            person['xml_id'] = None
        try:
            person['type'] = personelement.xpath('./@type')[0]
        except IndexError:
            person['type'] = None
        try:
            person['surname'] = personelement.xpath(
                './/tei:surname/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['surname'] = None
        try:
            person['forename'] = personelement.xpath(
                './/tei:forename/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['forename'] = None
        try:
            person['rolename'] = personelement.xpath(
                './/tei:roleName/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['rolename'] = None
        try:
            person['namelink'] = personelement.xpath(
                './/tei:nameLink/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['namelink'] = None
        names = personelement.xpath('.//tei:persName', namespaces=self.ns_tei)[1:]
        if names:
            person['alt_names'] = []
            for name in names:
                altname = {}
                altname['label'] = ", ".join(
                    [x.xpath('.//text()', namespaces=self.ns_tei)[0] for x in name]
                )
                try:
                    altname['type'] = name.xpath('./@subtype')[0]
                except IndexError:
                    altname['type'] = 'alt'
                person['alt_names'].append(altname)
        else:
            person['alt_names'] = []

        try:
            person['sex'] = personelement.xpath(
                './/tei:sex/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['sex'] = None

        try:
            person['birth_date'] = personelement.xpath(
                './tei:birth/@when-iso', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['birth_date'] = None
        try:
            person['birth_date_written'] = personelement.xpath(
                './tei:birth/tei:date/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['birth_date_written'] = None
        try:
            person['birth_place'] = personelement.xpath(
                './tei:birth/tei:placeName/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['birth_place'] = None
        try:
            person['death_date'] = personelement.xpath(
                './tei:death/@when-iso', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['death_date'] = None
        try:
            person['death_date_written'] = personelement.xpath(
                './tei:death/tei:date/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['death_date_written'] = None
        try:
            person['death_place'] = personelement.xpath(
                './tei:death/tei:placeName/text()', namespaces=self.ns_tei
            )[0]
        except IndexError:
            person['death_place'] = None

        idnos = personelement.xpath('.//tei:idno', namespaces=self.ns_tei)
        person['idnos'] = []
        if idnos:
            for idno in idnos:
                uri = {}
                try:
                    uri['domain'] = idno.xpath('./@type')[0]
                except IndexError:
                    uri['domain'] = None
                try:
                    uri['domain'] = idno.xpath('./@subtype')[0]
                except IndexError:
                    pass
                try:
                    uri['path'] = idno.xpath('./text()')[0]
                except IndexError:
                    uri['path'] = None
                person['idnos'].append(uri)
        if len(
            personelement.xpath('.//tei:occupation/text()', namespaces=self.ns_tei)
        ) > 0:
            person['occupation'] = personelement.xpath(
                './/tei:occupation/text()', namespaces=self.ns_tei
            )
        else:
            person['occupation'] = None

        return person

    def process_listperson(self, gnd=False):
        """ returns a list of person dicts """
        persons = self.parse_listperson(gnd=gnd)['persons']
        person_dicts = []
        for x in persons:
            person_dicts.append(self.person2dict(x))
        return person_dicts
