# fetal-surgery-disruptive-papers

Code to support identification of disruptive papers in Fetal Surgery.

- Compiles PubMed search hedges and queries from term lists
- Pulls search results from PubMed via NCBI Entrez API/PyMed library
- Maps PMIDs to Microsoft Academic Graph IDs (MAGID) via OpenAlex API
- Pulls top 100 citation counts, developmental scores, and disruption scores from the dataset created by 
Wu et al., 2021


# References

Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, 
venues, institutions, and concepts (arXiv:2205.01833). arXiv. https://doi.org/10.48550/arXiv.2205.01833

Sayers, E. (2010). A General Introduction to the E-utilities. In Entrez Programming Utilities Help 
[Internet]. National Center for Biotechnology Information (US). 
https://www.ncbi.nlm.nih.gov/books/NBK25497/

Wobben, G. (2022). PyMed—PubMed Access through Python [Python]. https://github.com/gijswobben/pymed 
(Original work published 2018)

Wu, L., Wang, D., & Evans, J. (2021). Replication Data for: Large teams develop and small teams disrupt 
science and technology [Data set]. Harvard Dataverse. https://doi.org/10.7910/DVN/JPWNNK

Wu, L., Wang, D., & Evans, J. A. (2019). Large teams develop and small teams disrupt science and 
technology. Nature, 566(7744), 378–382. https://doi.org/10.1038/s41586-019-0941-9


