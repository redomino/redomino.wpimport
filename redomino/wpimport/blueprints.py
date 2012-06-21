import logging
import urllib2
from StringIO import StringIO
import xml.etree.ElementTree as et
from lxml import html
from lxml import etree
from zope.interface import classProvides, implements
from Products.CMFCore.utils import getToolByName
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression
from DateTime import DateTime
from plone.i18n.normalizer import urlnormalizer as normalizer

xmlns_wp = "http://wordpress.org/export/1.1/"
xmlns_dc = "http://purl.org/dc/elements/1.1/"
xmlns_content = "http://purl.org/rss/1.0/modules/content/"
xmlns_excerpt = "http://wordpress.org/export/1.1/excerpt/"

typesMap = {
        'default' : 'Document', 
        'page' : 'Document',
        'post' : 'News Item',
    }

workflowMap = {
    'default' : '',
    'publish' : 'publish',
    'trash' : '',
    'inherit': '',
}

logger = logging.getLogger("redomino.wpimport")

class Source(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier



    def __iter__(self):
        data = self.transmogrifier.context.REQUEST.form['form.widgets.xml']
        data.seek(0)
#        import pdb ; pdb.set_trace()
#        filecontent = self.transmogrifier.context
#        xmlfile = filecontent.getFile()
#        if not filecontent.getContentType() == 'text/xml':
#            raise Exception('This file is not an xml')

#        data = StringIO(xmlfile.data)
        
        self.elements = (elem for action, elem in et.iterparse(data) if elem.tag == 'item')

        for i,elem in enumerate(self.elements):
            item = {}
            item['elem'] = elem

            logger.info("Importing content %s" % i )

            yield item

class GetWPType(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier

    def __iter__(self):
        for item in self.previous:
            elem = item['elem']
            wptype = elem.findtext(".//{%s}post_type" % xmlns_wp, default="")
            item['_wptype'] = wptype
            item['_type'] = typesMap.has_key(wptype) and typesMap[wptype] or typesMap['default']
            yield item


class Dictify(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.context = transmogrifier.context
        self.transmogrifier = transmogrifier

        self.base_path = self.context.REQUEST.form.get('form.widgets.base_path', '')

    def __iter__(self):
        for item in self.previous:
            elem = item['elem']
            item['link'] = elem.findtext("link", default="")
            item['title'] = elem.findtext("title", default="")
            normalized_title = normalizer.normalize(item['title'])

            wpid = elem.findtext(".//{%s}post_name" % xmlns_wp, default="")
#            item['id'] = wpid and wpid or normalized_title
            item['_id'] = str(normalized_title)

            wptype = elem.findtext(".//{%s}post_type" % xmlns_wp, default="")
            item['_type'] = typesMap.has_key(wptype) and typesMap[wptype] or typesMap['default']

            wpstatus = elem.findtext(".//{%s}status" % xmlns_wp, default="")
            item['_transitions'] = workflowMap.has_key(wpstatus) and workflowMap[wpstatus] or workflowMap['default']
            item['subject'] = [x.text for x in elem.findall("category")]
            creation_date = elem.findtext(".//{%s}post_date_gmt" % xmlns_wp, default="")

            pubDate = elem.findtext("pubDate", default="")
            item['effectiveDate'] = DateTime(pubDate)

            if creation_date and wptype == 'post':
                dt = DateTime(creation_date)
                item['creation_date'] = dt
                item['_path'] = "%(year)s/%(month)s/%(day)s/%(title)s" % { 'year': dt.year(),
                                                                           'month': dt.mm(),
                                                                           'day': dt.dd(),
                                                                           'title': normalized_title}
            else:
                item['_path'] = normalized_title

            item['_path'] = '/'.join((self.base_path, item['_path']))
            item['_path'] = str(item['_path'])
            item['description'] = elem.findtext(".//{%s}encoded" % xmlns_excerpt, default="")
            item['creators'] = elem.findtext(".//{%s}creator" % xmlns_dc, default="")
            item['text'] = elem.findtext(".//{%s}encoded" % xmlns_content, default="")
            item['attachment_url'] = elem.findtext(".//{%s}attachment_url" % xmlns_wp, default="")

            yield item


class BinaryData(object):
    """  """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.key = Expression(options['key'], transmogrifier, name, options)
        self.transmogrifier = transmogrifier

        self.context = transmogrifier.context
        self.base_path = self.context.REQUEST.form.get('form.widgets.base_path', '')

    def __iter__(self):
        for item in self.previous:
            key = self.key(item)
            if item.has_key(key) and item[key]:
                url = item[key]
                try: 
                    response = urllib2.urlopen(url)
                    filename = url.split('/')[-1]
                    item['_filename'] = filename
                    item['_id'] = str(filename)
                    item['_mimetype'] = response.headers.dict['content-type']
                    content_type = item['_mimetype'].startswith('image') and 'Image' or 'File' 
                    filename = url.split('/')[-1]
                    item['_path'] = url.split('wp-content/uploads')[-1]
                    if not item['_path']:
                        item['_path'] = '/'.join(item['_path'].split('/')[:-1] + [filename,])
                    item['_path'] = '/'.join((self.base_path, item['_path'].strip('/')))
                    item['_type'] = content_type
                    item['_datafield'] = content_type.lower()
                    item['_data'] = response.read()
                    logger.info("BINARY DATA IMPORTED!")

                except urllib2.HTTPError, e:
                    logger.warning("HTTPError [code:%s] [title:%s] [url:%s]" % (e.getcode(), item['title'], url))
                    continue
                except Exception, e:
                    logger.warning(e)
                    continue
            yield item

class Relinker(object):
    """  """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.context = transmogrifier.context
        self.catalog = getToolByName(self.context,'portal_catalog')

    def __iter__(self):
        for item in self.previous:
            if item['text']:
                tree = html.fromstring(item['text'])
                for img in tree.xpath('//img'):
                    objid = img.get('src').split('/')[-1]
                    res = self.catalog.searchResults(id=objid)
                    if len(res):
                        newhref = 'resolveuid/%s' % res[0].UID
                        logger.info('Rewriting img: [item:%s] [src:%s] [dst:%s]' % (item['_path'] , img.get('src'), newhref))
                        img.set('href', newhref) 
                        
                item['text'] = etree.tostring(tree, method='html', encoding=unicode)
            yield item
