# -*- coding: utf-8 -*-
"""
A python Client for connecting to the GSCF database
using the API as described in:
   http://old.studies.dbnp.org/api/
see also
    https://github.com/PhenotypeFoundation/GSCF-RClient/blob/master/dbnp.functions.R

>>> from GCSFClient import Session
>>> user = "username"
>>> passwd = "password"
>>> api_key = "api key"
>>> session = Session(user,passwd,api_key)

>>> # obtain it in pandas Dataframe format
>>> # need the pandas library installed
>>> # http://pandas.pydata.org/
>>> studies = session.getStudies(dataframe=True)

>>> # obtain the studies as a list of dictionaries
>>> studies = session.getStudies()

>>> print "found {} studies".format(len(studies))

>>> # choose the first study that contains PPS in the title
>>> # and load the subjects of the study
>>> study_token = studies.index[studies['title'].str.contains('PPS')][0]
>>> subjects = session.getSubjectsForStudy(study_token,dataframe=True)

>>> #get all the assays of a study
>>> assays = session.getAssaysForStudy(study_token)

>>> # take the first assay of a study
>>> # and load all the samples and measurements
>>> # if there is no readable dataset will raise
>>> # 401 - not authorized HTTPError
>>> assay_token = assays.index[0]
>>> samples = session.getSamplesForAssay(assay_token)
>>> measures = session.getMeasurementDataForAssay(assay_token)
"""

import md5
import urllib
import urllib2
import base64
import json
from uuid import getnode as get_mac
from contextlib import closing

class Session(object):
    """Instances of this class represents connections to the database GSCF
    it don't do any form of error chacking, as the urllib module raise a clear HTTPError
    if something goes wrong
    """
    def __init__(self, username, password, api_key, baseurl="http://studies.dbnp.org/api/"):
        """initialize the Session with the authentication credential on the given url"""
        #save the basic data
        self.user = username
        self.passwd = password
        self.apikey = api_key
        self.baseURL = baseurl
        #create the deviceID using the device mac address, a fixed string and the username
        base_string = 'GSCF database Python API'
        md5digest=md5.md5(str(get_mac())+base_string+username)
        self.deviceID = md5digest.hexdigest()
        #authenticate thyself to the server...do not really need a separate function
        self.authenticate()
        #try to load the pandas library for returning a DataFrame instead of
        #the JSON object. If pandas is not installed it will just disable the function,
        #not complains about it
        try:
            import pandas
            self.pandas = pandas
        except ImportError:
            self.pandas = None

    def authenticate(self):
        """make the authentication to the server
        raise HTTPError if something goes wrong"""
        req = urllib2.Request(self.baseURL+"authenticate")
        base64string = base64.encodestring('{}:{}'.format(self.user, self.passwd))[:-1]
        req.add_header("Authorization", "Basic {:s}".format(base64string))
        req.add_data("deviceID="+self.deviceID)
        #using a context manager to assure the closure of the resource
        with closing(urllib2.urlopen(req)) as handle:
            result = json.loads(handle.read())
            #save the results in self
            self.sequence = result['sequence']
            self.token = result['token']

    def __call__(self,action,options={}):
        """Call the GSCF api with the specified action (as a string) and the corresponding options
        it's a low level call that return a JSON object, so should not be used by the user directly"""
        #need to increment the sequence call each time
        #to keep the sincrony with the server
        self.sequence+=1
        #create the new validation key
        validate_md5 = md5.md5( self.token + str(self.sequence) + self.apikey )
        validation = validate_md5.hexdigest()
        #create the request
        req = urllib2.Request(self.baseURL+action)
        query_args = {"deviceID":self.deviceID, "validation":validation}
        query_args.update(options)
        req.add_data(urllib.urlencode(query_args))
        #obtain the results
        #using a context manager to assure the closure of the resource
        with closing(urllib2.urlopen(req)) as handle:
            res = json.loads(handle.read())
            return res

    def to_dataframe(self,data):
        """convert the given object to a pandas dataframe
        if the library is loaded, else raises an error"""
        if self.pandas:
            return self.pandas.DataFrame(data).set_index('token')
        else:
            raise ImportError("Pandas library (http://pandas.pydata.org/) is required for returning a dataframe")

    def getStudies(self,dataframe=False):
        res = self("getStudies")['studies']
        if dataframe: res = self.to_dataframe(res)
        return res

    def getSubjectsForStudy(self,study_token,dataframe=False):
        res = self('getSubjectsForStudy',{'studyToken':study_token})['subjects']
        if dataframe: res = self.to_dataframe(res)
        return res

    def getAssaysForStudy(self,assay_token,dataframe=False):
        res = self("getAssaysForStudy",{'studyToken':assay_token})['assays']
        if dataframe: res = self.to_dataframe(res)
        return res

    def getSamplesForAssay(self,assay_token,dataframe=False):
        res = self("getSamplesForAssay",{'assayToken':assay_token})["samples"]
        if dataframe: res = self.to_dataframe(res)
        return res

    def getMeasurementDataForAssay(self,assay_token,dataframe=False):
        res = self("getMeasurementDataForAssay",{'assayToken':assay_token})["measurements"]
        if dataframe:
            #the measurement data has a format different from the others, so must
            #be modified before converting it
            temp = [ dict([('token',k)]+v.items()) for k,v in res.iteritems()]
            res = self.to_dataframe(temp)
        return res

