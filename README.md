 
A python Client for connecting to the GSCF database
using the API as described in:

* <http://old.studies.dbnp.org/api/>

Is implemented in pure python (version 2.6 and above), and can leverage 
the pandas library for data analysis if installed.
To use install copy the file in your work directory (system wide install is not ready yet)

see also
    
* <https://github.com/PhenotypeFoundation/>

```python
>>> from GSCFClient import Session
>>> user = "username"
>>> passwd = "password"
>>> api_key = "api key"
>>> session = Session(user,passwd,api_key)

>>> # set dataframe to False will return the json list of dicts instead of the dataframe object
>>> # use only if you can't install the pandas library
>>> session = Session(user,passwd,api_key, dataframe=False)

>>> # connect to the old database (with the same API)
>>> session = Session(user,passwd,api_key, baseurl="http://old.studies.dbnp.org/api/")
>>> studies = session.getStudies()

>>> print "found {} studies".format(len(studies))

>>> # choose the studies that contains PPS in the title
>>> # and load the subjects of the first study
>>> tokens = studies.index[studies['title'].str.contains('PPS')]
>>> subjects = session.getSubjectsForStudy(tokens[0])

>>> # to load the subjects of multiple studies at the same time
>>> # just pass a list of tokens
>>> # note the asterisk to explode the list!
>>> subjects = session.getSubjectsForStudy(*tokens)
>>> # equivalent sintax
>>> subjects = session.getSubjectsForStudy(tokens[0],tokens[1])

>>> #get all the assays of a study
>>> assays = session.getAssaysForStudy(tokens[0])

>>> # take the first assay of a study
>>> # and load all the samples and measurements
>>> # if there is no readable dataset will raise
>>> # 401 - not authorized HTTPError
>>> assay_token = assays.index[0]
>>> samples = session.getSamplesForAssay(assay_token)
>>> measures = session.getMeasurementDataForAssay(assay_token)
```