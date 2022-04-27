__author__ = "marijane white, whimar@ohsu.edu"
# import argparse
from asyncore import write
from datetime import date
import glob
import logging
from pathlib import Path
from urllib.error import HTTPError
import pandas as pd
from pymed import PubMed
import requests
import time
from tqdm import tqdm

logging.basicConfig(
    filename="logfile.txt",
    filemode="w",
    force=True,
    format="%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()

# TODO: accept and parse command line arguments for email, user-defined field tags, max results

# endpoints and HTTP headers
email = "whimar@oshu.edu"
pubmed = PubMed(tool="FetalSurgerySearch", email=email)
openalex = "https://api.openalex.org/works/pmid:"
headers = {"user-agent": "mailto:" + email}
max_results = 210000
datestamp = time.strftime("%Y%m%d")

# directory paths
KW_ROOT = "keywords/*"
MH_ROOT = "mesh-terms/*"
T_ROOT = "target/"
C_ROOT = T_ROOT + "csv/"
H_ROOT = T_ROOT + "hedges/"
P_ROOT = T_ROOT + "pmid/"
Q_ROOT = T_ROOT + "queries/"

# mkdirs if not exist
Path(T_ROOT).mkdir(parents=True, exist_ok=True)
Path(C_ROOT).mkdir(parents=True, exist_ok=True)
Path(H_ROOT).mkdir(parents=True, exist_ok=True)
Path(P_ROOT).mkdir(parents=True, exist_ok=True)
Path(Q_ROOT).mkdir(parents=True, exist_ok=True)

# TODO: use https://pypi.org/project/pmidcite/ to pull iCite citation data
# TODO: use https://pypi.org/project/venn/ to draw venn diagrams of searches


def runhedge(hedge, bblock, hedgetype):
    hedgecount = str(pubmed.getTotalResultsCount(hedge))
    hedgefile = f"{H_ROOT}{datestamp}-{bblock}-{hedgecount}-{hedgetype}.txt"
    with open(hedgefile, "w+") as f:
        f.write(f"({hedge})")
    logger.info("  building block\t: %s", bblock)
    logger.info("  hedge type\t\t: %s", hedgetype)
    logger.info("  hedge results\t: %s", hedgecount)
    logger.info("  hedge file\t\t: %s", hedgefile)
    logger.info("  hedge\t\t\t: %s", hedge)


def runquery(query, querytype):
    try:
        querycount = str(pubmed.getTotalResultsCount(query))
    except requests.exceptions.HTTPError as httperr:
        logger.error(httperr)
        queryfile = f"{Q_ROOT}{datestamp}-{querytype}-TOOLONG.txt"
        with open(queryfile, "w+") as f:
            f.write(query)
        return
    except Exception as e:
        logger.error("e.message")

    queryfile = f"{Q_ROOT}{datestamp}-{querycount}-{querytype}.txt"
    with open(queryfile, "w+") as f:
        f.write(query)
    logger.info("query results\t\t: %s", querycount)
    logger.info("query file\t\t\t: %s", queryfile)
    logger.info("query\t\t\t\t: %s", query)

    results = pubmed.query(query, max_results=max_results)
    articles = [
        [
            article.pubmed_id.splitlines()[0],
            article.title,
            article.journal,
            article.publication_date,
            article.doi,
            article.abstract,
        ]
        for article in tqdm(results, total=int(querycount), desc=querytype)
        if hasattr(article, "journal")
    ]
    articlecount = len(articles)
    logger.info("  article count\t: %s", articlecount)

    df = pd.DataFrame(
        articles,
        columns=["pmid", "title", "journal", "pubdate", "doi", "abstract"],
    )
    df.set_index(["pmid"])
    df["doi"] = [f'=HYPERLINK("https://doi.org/{doi}")' for doi in df["doi"]]
    df["pubmed url"] = [
        f'=HYPERLINK("https://www.ncbi.nlm.nih.gov/pubmed/{pmid}")'
        for pmid in df["pmid"]
    ]
    df["ohsu library"] = [
        f'=HYPERLINK("https://librarysearch.ohsu.edu/openurl/OHSU/OHSU?sid=Entrez:PubMed&id=pmid:{pmid}")'
        for pmid in df["pmid"]
    ]
    df["rush library"] = [
        f'=HYPERLINK("=HYPERLINK("https://i-share-rsh.primo.exlibrisgroup.com/openurl/01CARLI_RSH/01CARLI_RSH:CARLI_RSH?sid=Entrez:PubMed&id=pmid:{pmid}")'
        for pmid in df["pmid"]
    ]
    csvfile = f"{C_ROOT}{datestamp}-{articlecount}-{querytype}.csv"
    pmidfile = f"{P_ROOT}{datestamp}-{articlecount}-{querytype}.txt"
    df.to_csv(csvfile, index=False)
    df[["pmid"]].to_csv(pmidfile, index=False, header=False)
    logger.info("  csv file\t\t\t: %s", csvfile)
    logger.info("  pmid file\t\t: %s", pmidfile)

    def map_to_mag(csvfile, magfile, nomagfile):
        df = pd.DataFrame.read_csv(csvfile)
        pmids = df["pmid"]

        # TODO: add magid column to datafrane
        mags = []
        nomag_pmids = []
        for pmid in tqdm(pmids, desc="openalex"):
            response = requests.get(openalex + pmid, headers=headers)
            if response.status_code == 200:
                work = response.json()
                if "mag" in work["ids"]:
                    mags.append(work["ids"]["mag"])
                else:
                    nomag_pmids.append(pmid)
            else:
                nomag_pmids.append(pmid)

        # save them in the target root dir
        with open(magfile, "w") as f:
            f.write("\n".join(mags))

        with open(nomagfile, "w") as f:
            f.write("\n".join(nomag_pmids))


if __name__ == "__main__":
    logger.info("BEGIN")
    # build mesh hedges from mesh term lists and save them to text
    mh_hedges = []
    mh_termfiles = sorted(glob.glob(MH_ROOT))
    for mh_termfile in mh_termfiles:
        logger.info("term file\t\t\t: %s", mh_termfile)
        bblock = Path(mh_termfile).stem
        with open(mh_termfile, "r") as f:
            mh_hedge = " OR ".join(sorted(f.read().strip().split("\n")))
            runhedge(mh_hedge, bblock, "mesh")
            mh_hedges.append(f"({mh_hedge})")

    # build mesh-only query from mesh hedges
    mh_query = " AND ".join(mh_hedges)
    runquery(mh_query, "mesh")

    # build keyword hedges from keyword term lists and save them to text
    # field_tags = ["[all]", "[tw]", "[tiab]"] # [all] is broken?
    field_tags = ["[tw]", "[tiab]"]
    kw_termfiles = sorted(glob.glob(KW_ROOT))
    for field_tag in field_tags:
        kw_hedges = []
        kwNOTmedline_hedges = []
        mh_kw_hedges = []
        for (kw_termfile, mh_hedge) in zip(kw_termfiles, mh_hedges):
            logger.info("term file\t\t\t: %s", kw_termfile)
            bblock = Path(kw_termfile).stem
            kws = []
            with open(kw_termfile) as f:
                kws = sorted(f.read().split("\n"))
            for i, kw in enumerate(kws):
                # tag each term in any multi-term searches
                if " " in kw and '"' not in kw:
                    wordlist = kw.split()
                    words = [word + field_tag for word in wordlist]
                    kws[i] = f"({' '.join(words)})"
                else:
                    # tag single-term searches
                    kws[i] = f"{kw}{field_tag}"
                kw_hedge = f"{' OR '.join(kws)}"
            runhedge(kw_hedge, bblock, f"keyword{field_tag}")
            kw_hedges.append(f"({kw_hedge})")

            # subtract medline subset from keyword query
            kwNOTmedline_hedge = f"({kw_hedge}) NOT (medline[sb])"
            runhedge(kwNOTmedline_hedge, bblock, f"keyword{field_tag}NOTmedline")
            kwNOTmedline_hedges.append(f"({kwNOTmedline_hedge})")

            # combine each pair of mesh and keyword building blocks with OR
            mh_kw_hedge = f"{mh_hedge} OR ({kw_hedge})"
            runhedge(mh_kw_hedge, bblock, f"meshORkeyword{field_tag}")
            mh_kw_hedges.append(f"({mh_kw_hedge})")

        # build keyword-only query
        kw_query = " AND ".join(kw_hedges)
        runquery(kw_query, f"keyword{field_tag}")

        # build keywordNOTmedline query
        kwNOTmedline_query = " AND ".join(kwNOTmedline_hedges)
        runquery(kwNOTmedline_query, f"keyword{field_tag}NOTmedline")

        # build mesh OR keyword query
        mh_kw_query = " AND ".join(mh_kw_hedges)
        runquery(mh_kw_query, f"mesh-keyword{field_tag}")

        # combine entire mesh query with entire keyword query
        mhORkw_query = f"({mh_query}) OR ({kw_query})"
        runquery(mhORkw_query, f"meshORkeyword{field_tag}")

        # combine entire mesh query with entire keywordNOTmedlinequery
        mhORkwNOTmedline_query = f"({mh_query}) OR ({kwNOTmedline_query})"
        runquery(mhORkwNOTmedline_query, f"meshORkeyword{field_tag}NOTmedline")

    logger.info("END")
