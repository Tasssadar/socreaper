#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests,json,sys,codecs,sqlite3,os
from BeautifulSoup import *

BASE_ADDRESS="http://soc.nidv.cz"

def get_page(addr):
    req = requests.get(addr)
    if req.status_code != 200:
        raise Exception("failed to get %s: %s"  % (addr, str(req.status_code)))

    req.encoding="utf-8"
    html = re.sub(r'&(?!amp;)', r'&amp;', req.text)
    return BeautifulSoup(html)

def get_year_addresses():
    soup = get_page(BASE_ADDRESS + "/archiv")

    displayContent = soup.find("div", id="displayContent")
    linksDiv = displayContent.find("div")
    links = linksDiv.findAll("a")

    addresses = []
    for l in links:
        if l["href"].startswith("/archiv/"):
            addresses.append({"addr": BASE_ADDRESS + l["href"], "season": int(l["href"][-2:]) })
    return addresses


def reap_season(season, addr):
    soup = get_page(addr)
    displayContent = soup.find("div", id="displayContent")
    linksDiv = displayContent.find("div", attrs={"style": "padding: 20px;"})
    links = linksDiv.findAll("a")

    res = {
        "season": season,
        "year": 1978 + season,
        "theses": [],
    }

    for l in links:
        if not l["href"].startswith("/archiv/"):
            continue

        sys.stderr.write(u"  Reaping field %s\n" % l.string.strip())
        res["theses"].extend(reap_field(BASE_ADDRESS + l["href"]))
    return res

def fixup_link(addr):
    if addr.startswith("/"):
        return BASE_ADDRESS + addr
    return addr

def reap_field(addr):
    res = []
    idx = addr[addr.rfind("/")+1:]
    soup = get_page(addr)
    displayContent = soup.find("div", id="displayContent")

    aTitle = displayContent.find("a", attrs={"name": "obor" + idx})
    fieldName = aTitle.h3.string

    olTheses = displayContent.findAll("li")
    place = 1
    for th in olTheses:
        thesis = {
            "title": th.strong.string,
            "place": place,
            "description": th.div.string.strip(),
            "field": fieldName,
            "published": True,
        }

        if th.b and th.b.string.strip() == u"Autor/ři nedal/i souhlas se zveřejnením práce.":
            thesis["published"] = False

        authorsPrefix = u'Autor/ři: '
        for c in th.contents:
            try:
                c = c.strip()
                if c.startswith(authorsPrefix):
                    thesis["authors"] = c[len(authorsPrefix):]
            except TypeError:
                continue

        for a in th.findAll("a"):
            text = a.string.strip()
            if text == u"Text práce ve formátu PDF":
                thesis["pdf"] = fixup_link(a["href"])
            elif text == u"stáhnout přílohu":
                thesis["attachment"] = fixup_link(a["href"])

        if "pdf" not in thesis and thesis["published"]:
            print "link to pdf for thesis %s on page %s not found!" % (thesis["title"], addr)
            raise Exception()

        res.append(thesis)
        place += 1
    return res

def dump_to_sqlite(results, path):
    try:
        os.remove(path)
    except:
        pass

    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute('''CREATE TABLE `socky` (
        `year`  INTEGER NOT NULL,
        `season`        INTEGER NOT NULL,
        `field` TEXT,
        `place` INTEGER NOT NULL,
        `title` TEXT NOT NULL,
        `authors`       TEXT NOT NULL,
        `description`   TEXT,
        `pdf`   TEXT,
        `attachment`    TEXT
    );''')

    for season in results:
        for th in season["theses"]:
            pdf = th["pdf"] if "pdf" in th else ""
            attachment = th["attachment"] if "attachment" in th else ""
            c.execute('INSERT INTO socky VALUES (?,?,?,?,?,?,?,?,?);',
                (season["year"], season["season"], th["field"], th["place"], th["title"], th["authors"], th["description"], pdf, attachment))

    c.execute('CREATE INDEX sockyYearIdx ON socky(year);');
    c.execute('CREATE INDEX sockyTitleIdx ON socky(title);');
    c.execute('CREATE INDEX sockySeasonIdx ON socky(season);');
    c.execute('CREATE INDEX sockyFieldIdx ON socky(field);');
    c.execute('CREATE INDEX sockyDescriptionIdx ON socky(description);');
    c.execute('CREATE INDEX sockyAuthorsIdx ON socky(authors);');
    conn.commit()
    conn.close()

if __name__ == "__main__":
    UTF8Writer = codecs.getwriter('utf8')
    sys.stdout = UTF8Writer(sys.stdout)
    sys.stderr = UTF8Writer(sys.stderr)

    if len(sys.argv) >= 2:
        f = open(sys.argv[1], 'r')
        res = json.load(f)
        dump_to_sqlite(res, sys.argv[2])
    else:
        addresses = get_year_addresses()
        res = []
        for season in addresses:
            sys.stderr.write("Reaping season %s\n" % season["season"])
            res.append(reap_season(season["season"], season["addr"]))
        json.dump(res, sys.stdout, indent=2, ensure_ascii=False, encoding="utf-8")
