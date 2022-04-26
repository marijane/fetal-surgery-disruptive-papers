__author__ = "marijane white, whimar@ohsu.edu"
# import argparse
import glob
import logging
from logging.config import dictConfig
from pathlib import Path
import pandas as pd
from pymed import PubMed
import requests
from tqdm import tqdm

# TODO: accept and parse command line arguments for email, user-defined field tags

logging_config = dict(
    version=1,
    formatters={"f": {"format": "%(asctime)s %(levelname)-6s %(message)s"}},
    handlers={
        "h": {
            "class": "logging.StreamHandler",
            "formatter": "f",
            "level": logging.DEBUG,
        }
    },
    root={"handlers": ["h"], "level": logging.DEBUG},
)
dictConfig(logging_config)
logger = logging.getLogger()

# endpoints and HTTP headers
email = "whimar@oshu.edu"
pubmed = PubMed(tool="FetalSurgerySearch", email=email)
openalex = "https://api.openalex.org/works/pmid:"
headers = {"user-agent": "mailto:" + email}
max_results = 210000

# directory paths
kw_root = "keywords/*"
mh_root = "mesh-terms/*"
t_root = "target/"
c_root = t_root + "csv/"
p_root = t_root + "pmid/"
q_root = t_root + "queries/"

# TODO: create directories if they don't exist
# TODO: write a function to create dated snapshots of queries and results
# TODO: use https://pypi.org/project/pmidcite/ to pull iCite citation data
# TODO: use https://pypi.org/project/venn/ to draw venn diagrams of searches


def writefiles(query, queryfile, csvfile, pmidfile):
    with open(q_root + queryfile, "w+") as f:
        f.write(query)

    logger.info(queryfile)
    num_results = pubmed.getTotalResultsCount(query)
    logger.info(num_results)
    # results = pubmed.query(query, max_results=max_results)
    # articles = [
    #     [
    #         article.pubmed_id.splitlines()[0],
    #         article.title,
    #         article.journal,
    #         article.publication_date,
    #         article.doi,
    #         article.abstract,
    #     ]
    #     for article in tqdm(results, total=num_results)
    #     if hasattr(article, "journal")
    # ]
    # df = pd.DataFrame(
    #     articles,
    #     columns=["pmid", "title", "journal", "pubdate", "doi", "abstract"],
    # )
    # df.set_index(["pmid"])
    # df["pubmed url"] = (
    #     '=HYPERLINK("https://www.ncbi.nlm.nih.gov/pubmed/' + df["pmid"] + '")'
    # )
    # df["ohsu library search"] = (
    #     '=HYPERLINK("https://librarysearch.ohsu.edu/openurl/OHSU/OHSU?sid=Entrez:PubMed&id=pmid:'
    #     + df["pmid"]
    #     + '")'
    # )
    # df["rush library search"] = (
    #     '=HYPERLINK("https://i-share-rsh.primo.exlibrisgroup.com/openurl/01CARLI_RSH/01CARLI_RSH:CARLI_RSH?sid=Entrez:PubMed&id=pmid:'
    #     + df["pmid"]
    #     + '")'
    # )
    # num_articles = len(articles)
    # df.to_csv(c_root + str(num_articles) + "-" + csvfile, index=False)
    # df[["pmid"]].to_csv(
    #     p_root + str(num_articles) + "-" + pmidfile, index=False, header=False
    # )


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

    # build mesh hedges from mesh term lists
    mh_files = sorted(glob.glob(mh_root))
    mh_hedges = [
        "(" + " OR ".join(open(mh_file).read().split("\n")) + ")"
        for mh_file in mh_files
    ]
    # build mesh-only query from mesh hedges
    mh_query = " AND ".join(mh_hedges)
    mh_queryfile = "mh.txt"
    mh_csvfile = "mh.csv"
    mh_pmidfile = "mh-pmids.txt"
    writefiles(mh_query, mh_queryfile, mh_csvfile, mh_pmidfile)

    # build keyword hedges from keyword term lists
    kw_files = sorted(glob.glob(kw_root))
    # field_tags = ["[tiab]", "[tw]", "[all]"]
    field_tags = ["[tiab]", "[tw]", "[all]"]
    for tag in field_tags:
        kw_hedges = [
            "(" + " OR ".join([kw + tag for kw in kw_list]) + ")"
            for kw_list in [open(kw_file).read().split("\n") for kw_file in kw_files]
        ]
        mh_kw_hedges = [
            "(" + " OR ".join([mh_hedges[i], kw_hedges[i]]) + ")"
            for i in range(len(mh_hedges))
        ]

        # keywords
        kw_query = " AND ".join(kw_hedges)
        kw_file = "kw" + tag
        kw_queryfile = kw_file + ".txt"
        kw_csvfile = kw_file + ".csv"
        kw_pmidfile = kw_file + "-pmid.txt"
        writefiles(kw_query, kw_queryfile, kw_csvfile, kw_pmidfile)

        # keywordsNOTmedline
        kwNOTmedline_query = kw_query + " NOT medline[sb]"
        kwNOTmedline_file = "kw" + tag + "NOTmedline"
        kwNOTmedline_queryfile = kwNOTmedline_file + ".txt"
        kwNOTmedline_csvfile = kwNOTmedline_file + ".csv"
        kwNOTmedline_pmidfile = kwNOTmedline_file + "-pmid.txt"
        writefiles(
            kwNOTmedline_query,
            kwNOTmedline_queryfile,
            kwNOTmedline_csvfile,
            kwNOTmedline_pmidfile,
        )

        # (mesh)OR(keywords)
        mh_OR_kw_query = "(" + mh_query + ") OR (" + kw_query + ")"
        mh_OR_kw_file = "(mh)OR(kw" + tag + ")"
        mh_OR_kw_queryfile = mh_OR_kw_file + ".txt"
        mh_OR_kw_csvfile = mh_OR_kw_file + ".csv"
        mh_OR_kw_pmidfile = mh_OR_kw_file + "-pmid.txt"
        writefiles(
            mh_OR_kw_query, mh_OR_kw_queryfile, mh_OR_kw_csvfile, mh_OR_kw_pmidfile
        )

        # (mesh)OR(keywordsNOTmedline)
        mh_OR_kwNOTmedline_query = "(" + mh_query + ") OR (" + kwNOTmedline_query + ")"
        mh_OR_kwNOTmedline_file = "(mh)OR(kw" + tag + "NOTmedline)"
        mh_OR_kwNOTmedline_queryfile = mh_OR_kwNOTmedline_file + ".txt"
        mh_OR_kwNOTmedline_csvfile = mh_OR_kwNOTmedline_file + ".csv"
        mh_OR_kwNOTmedline_pmidfile = mh_OR_kwNOTmedline_file + "-pmid.txt"
        writefiles(
            mh_OR_kwNOTmedline_query,
            mh_OR_kwNOTmedline_queryfile,
            mh_OR_kwNOTmedline_csvfile,
            mh_OR_kwNOTmedline_pmidfile,
        )

        # (meshORkeywords)
        mhORkw_query = " AND ".join(mh_kw_hedges)
        mhORkw_file = "mhORkw" + tag
        mhORkw_queryfile = mhORkw_file + ".txt"
        mhORkw_csvfile = mhORkw_file + ".csv"
        mhORkw_pmidfile = mhORkw_file + "-pmid.txt"
        writefiles(mhORkw_query, mhORkw_queryfile, mhORkw_csvfile, mhORkw_pmidfile)
