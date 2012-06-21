"""
Wordpress import view
"""
from zope.interface import implements, Interface
from zope import schema

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.transmogrifier.transmogrifier import Transmogrifier
from collective.transmogrifier.transmogrifier import \
    configuration_registry as cr

from z3c.form import form, field, button, interfaces
from z3c.form.browser.radio import RadioWidget

from redomino.wpimport import _

from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from plone.z3cform.layout import wrap_form

from Products.CMFCore.utils import getToolByName

ownership_vocab = SimpleVocabulary(
        [SimpleTerm(value=u'1', title=_(u'Take ownership of imported objects')),
         SimpleTerm(value=u'2', title=_(u'Retain existing ownership information'))
        ]
    )

class IWPImport(Interface):
    """ Form interface """


    base_path = schema.TextLine(
        title=_(u"Base import path"),
        required=False,
        description=_(u"Insert a base path where all imported contents will be placed"),
    )

    takeownership = schema.Choice(
        title=_(u"Ownership"),
        description=_(u"The skin that should be used for the ZMI."),
        vocabulary=ownership_vocab
    )

    xml = schema.Bytes(title=u'Wordpress xml file')


class WPImportForm(form.Form):
    implements(IWPImport)
    fields = field.Fields(IWPImport)
#    fields['takeownership'].widgetFactory = RadioWidget
    ignoreContext = True # don't use context to get widget data
    label = _(u"Wordpress import")
    
    def update(self):
        # disable Plone's editable border
        self.request.set('disable_border', True)
        super(WPImportForm, self).update()

    @button.buttonAndHandler(_(u"Submit"))
    def handleSubmit(self, action):
        data, errors = self.extractData()

        purl = getToolByName(self.context, 'portal_url')
        portal = purl.getPortalObject()

        transmogrifier = Transmogrifier(portal)

        transmogrifier('redomino.wpimport.binarydata-import')
        transmogrifier('redomino.wpimport.import')
        
        

    def getFile(self, fieldname):
        form = self.request.form
        filewrapper = form['form.widgets.%s' % fieldname]

        data = filewrapper.seek(0)
        data = filewrapper.read()
        if not data:
            return None
        filename = filewrapper.filename
        title = form['form.widgets.%s_title' % fieldname]

        obj_id = urlnormalizer.normalize(filename)
        obj_id = self.getValidIdFromContext(self.context, obj_id)
        obj_id = self.context.invokeFactory('File', id=obj_id)
        obj = self.context[obj_id]
        obj.setTitle(title)
        obj.setFile(data)
        obj.setFilename(filename)
        obj.getField('file').setContentType(obj, self.getMimetype(filename))
        return obj


WordpressImportFormView = wrap_form(WPImportForm)



