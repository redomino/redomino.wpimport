import xml.etree.ElementTree as et

#tree = et.iterparse("mastrolinux.wordpress.2012-04-04.xml")

tree = et.iterparse("obiettivomondo.wordpress.2012-04-10.xml")

wp = "http://wordpress.org/export/1.1/"
dc ="http://purl.org/dc/elements/1.1/"
content="http://purl.org/rss/1.0/modules/content/"

#dict(zip(a, map(elem.findtext, b)))
def set_attrs(elem):
    item = {}
    item['link'] = elem.findtext("link", default="")
    item['title'] = elem.findtext("title", default="")
    item["_transitions"] = elem.findtext(".//{%s}status" % wp, default="")
    item['subject'] = [x.text for x in elem.findall("category")]
    item['creation_date'] = elem.findtext(".//{%s}post_date_gmt" % wp, default="")
    item['description'] = elem.findtext("description", default="")
    item['creators'] = elem.findtext("creator", default="")
    item['text'] = elem.findtext(".//{%s}encoded" % content, default="")
    item['Document'] = elem.findtext(".//{%s}post_type" % wp, default="")
    item['attachment_url'] = elem.findtext(".//{%s}attachment_url" % wp, default="")
    return item

for action, elem in tree:
    if elem.tag == "item":
        print set_attrs(elem)
        elem.clear()






