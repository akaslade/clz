from .base import make_picture_url
from .desc import make_description
from .categoryids import make_superhero_table

# These are not required fields!
EbayFields = ['Title', 'Subtitle', 'PicURL',
              'Description',
              'Product:UPC',
              'Product:ISBN',
]

def makeCommonData(config):
    CommonData = dict()
    # we will use PostalCode for location
    rlocation = False
    need_rlocation = True
    for field, value in config.items('reqfields'):
        rfield = '*%s' % field.capitalize()
        CommonData[rfield] = value
        if field.lower() == 'location':
            rlocation = True
            need_rlocation = False
    if not rlocation:
        optfields = [o.lower() for o in config.options('optfields')]
        if 'postalcode' not in optfields:
            raise RuntimeError, "need postal code if not using location"
        code = config.get('optfields', 'postalcode')
        CommonData['PostalCode'] = code
        need_rlocation = False
    if need_rlocation and not rlocation:
        raise RuntimeError, "another problem"
    for field in config.options('optfields'):
        CommonData[field] = config.get('optfields', field)
    return CommonData

def make_age_range(config, age):
    yrange = config.get('comic_ages', age)
    start, end = [int(y.strip()) for y in yrange.split(',')]
    return range(start, end + 1)
    
def find_age(config, year):
    year = int(year)
    ages = config.options('comic_ages')
    for age in ages:
        r = make_age_range(config, age)
        if year in make_age_range(config, age):
            return age
    return None

def get_category_id(config, comic, opts):
    shtable = make_superhero_table(config)
    heroidx = 4
    ageidx = 1
    catidx = 0
    category = opts.category
    year = comic.publicationdate.displayname.string
    age = find_age(config, year)
    if age is None:
        raise RuntimeError, "Unknown age for year %s" % year
    #print "YEAR", year, age
    age_rows = [r for r in shtable if r[ageidx] == age]
    other_row = [r for r in age_rows if r[heroidx].startswith('Other')]
    if len(other_row) > 1:
        raise RuntimeError, "too many other rows for age %s" % age
    other_row = other_row[0]
    seriesname = comic.series.displayname.string.lower()
    found_row = other_row
    for row in age_rows:
        hero = row[heroidx].lower()
        if hero in seriesname:
            found_row = row
            break
    #print "Found Row is", found_row
    if False and found_row[heroidx].startswith('Other'):
        print "OTHER", seriesname
    return found_row[catidx]

def make_title(comic):
    title = comic.series.displayname.string
    if len(title) > 80:
        raise RuntimeError, "Title too long %s" % comic.id.string
    return title


def make_subtitle(comic):
    if comic.fulltitle is not None:
        subtitle =  comic.fulltitle.string
    elif comic.edition is not None:
        subtitle = comic.edition.displayname.string
    elif comic.description is not None:
        subtitle = comic.description.string
    else:
        import pdb ; pdb.set_trace()
        
def makeEbayInfo(config, comic, opts):
    data = makeCommonData(config)
    Title = make_title(comic)
    Subtitle = make_subtitle(comic)
    urlprefix = config.get('main', 'urlprefix')
    PicURL = make_picture_url(comic.coverfront.string, urlprefix)
    Description = make_description(config, comic)
    ndata = dict(Title=Title,
                 Subtitle=Subtitle,
                 PicURL=PicURL,
                 Description=Description,
    )
    #ndata['Product:Brand'] = comic.publisher.displayname.string
    if comic.isbn is not None:
        ndata['Product:ISBN'] = comic.isbn.string
    if comic.barcode is not None:
        ndata['Product:UPC'] = comic.barcode.string
    data.update(ndata)
    Quantity = int(comic.quantity.string)
    if Quantity > config.getint('reqfields', 'quantity'):
        data['*Quantity'] = Quantity
    data['*Category'] = get_category_id(config, comic, opts)
    return data
