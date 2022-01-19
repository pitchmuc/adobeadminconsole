import json, time
from copy import deepcopy
import pandas as pd
from adobeadminconsole import connector,config
import logging
import os
from typing import Union,IO

class AdminConsole:
    """
    Class that encapsulates the different methods available for the Admin Console module.
    It automatically generates a token when the class is instanciated.
    """

    loggingEnabled = False
    logger = None

    def __init__(self,config_object: dict = config.config_object, header: dict = config.header, loggingObject:dict=None):
        """
        Instancialize the class and retrieve the token
        """
        if loggingObject is not None and sorted(["level","stream","format","filename","file"]) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}.analytics")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter(loggingObject["format"])
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)
        self.connector = connector.AdobeRequest(
            config_object=config_object, header=header,loggingEnabled=self.loggingEnabled,logger=self.logger)
        self.header = self.connector.header
        self.endpoint = config.endpoints['global']
        self.orgId = config.config_object['org_id']

    def getUsers(self)->pd.DataFrame:
        """
        Retrieve the users from the Admin Console
        """
        path = f"/users/{self.orgId}"
        last_page = False
        page = 0 # start of the loop
        list_users = []
        while last_page != True:
            res = self.connector.getData(self.endpoint + path + f"/{page}")
            list_users += res['users']
            page +=1
            last_page = res.get("lastPage", True)
        df = pd.DataFrame(list_users)
        df.fillna('',inplace=True)
        return df


    def getGroups(self)->dict:
        """
        Retrieve the groups located in the Admin Console
        """
        path = f"/groups/{self.orgId}"
        last_page = False
        page = 0 # start of the loop
        list_groups = []
        while last_page != True:
            res = self.connector.getData(self.endpoint + path + f"/{page}")
            list_groups += res['groups']
            page +=1
            last_page = res.get("lastPage", True)
        df = pd.DataFrame(list_groups)
        df.fillna('',inplace=True)
        return df
    
    def createTemplates(self, fileType='csv',verbose=False):
        """ 
        Create template files for user and group details.
        2 types of file can be created, it will be defined by the fileType. 
        fileType : REQUIRED : 2 possible values : 
            - 'csv' : different files in csv format
            - 'xlsx' : one excel file with different format
        verbose : Default False. If set to True, print information.
        """
        df_template_new_user = {'email':['email-address'],'firstname':['OPTIONAL'],'lastname':['OPTIONAL'],'country':['OPTIONAL : Country Code']}
        df_template_new_group = {'name':['group-name'],'description':['OPTIONAL']}
        template_new_users = pd.DataFrame(df_template_new_user)
        template_new_group = pd.DataFrame(df_template_new_group)
        if fileType == 'xlsx':
            writer = pd.ExcelWriter(os.cwd() +'/template_users_groups.xlsx', engine='xlsxwriter')
            template_new_users.to_excel(writer,sheet_name='new_users',index=False)
            template_new_group.to_excel(writer,sheet_name='new_groups',index=False)
            writer.save()
        elif fileType == 'csv':
            template_new_users.to_csv('new_users.csv', index=False,sep='\t')
            template_new_group.to_csv('new_groups.csv', index=False,sep='\t')
        if verbose==True:
            print('Template Files have been created in : '+ os.cwd())
    
    def findProducts(self, groups:Union[pd.DataFrame, IO]=None,delimiter:str=',')->list:
        """ 
        Find the products that are attached to this account by screening the groups dataframe.
        Arguments: 
            groups : REQUIRED : Dataframe, or CSV file, or XSLX file of the group information retrieved
                Excel file expects a sheet_name called "groups_infos"
            delimiter : OPTIONAL : the delimiter to be used for CSV file
        returns a list of product
        """
        if groups is not None and isinstance(groups,pd.DataFrame) == True:
            df_groups = groups
        elif groups is not None and '.csv' in groups:
            df_groups = pd.read_csv(groups,delimiter=delimiter)
        elif groups is not None and '.xlsx' in groups:
            df_groups = pd.read_excel(groups,sheet_name='groups_infos')
        products = set(df_groups['productName'])
        if '' in products:
            products.remove('')
        list_product = list(products)
        return list_product
    
    def createUser(self,email:str=None,userType:str=None,firstname:str='',lastname:str='', countryCode:str=None,test:bool=False)->dict:
        """
        Create a new user base on his email address.
        Arguments:
            email : REQUIRED : email address.
            userType : REQUIRED : either one of these values adobeID, enterpriseID or federatedID
            firstname : OPTIONAL : the first name (required for Enterprise and Federated ID)
            lastname : OPTIONAL : the last name (required for Enterprise and Federated ID)
            country : OPTIONAL : Country Code (required for Federated ID)
            test : OPTIONAL : If you want to test the method
        """
        if email is None:
            raise ValueError("Require an email address")
        if userType is None:
            raise ValueError("Should be either adobeID, enterpriseID or federatedID")
        if userType == "adobeID":
            creation = {
                "addAdobeID": {  
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname,
                    "option" : "updateIfAlreadyExists"
                }
            }
        elif userType == "enterpriseID":
            creation = {
                "createEnterpriseID": {  
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname,
                    "option" : "updateIfAlreadyExists"
                }
            }
        elif userType == "federatedID":
            creation = {
                "createFederatedID": {  
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname,
                    "country":countryCode,
                    "option" : "updateIfAlreadyExists"
                }
            }
        message = [
            {
                'user':email,
                'requestID' : 'action1',
                "do":[
                    creation
                ] 
            }
        ]
        if test:
            parameter = {'testOnly':'true'}
        else:
            parameter = {}
        path = f"/action/{self.orgId}"
        res = self.connector.postData(self.endpoint+path,params=parameter,data=message)
        return res

    def removeUser(self,email:str=None,test:bool=False)->dict:
        """
        Remove users from the Admin Console, stripping it from every groups.
        Argument:
            email : REQUIRED : The email address of the user.
            test : OPTIONAL : If you want to test the method
        """
        if email is None:
            raise ValueError("Require an email address")
        message = [{
            "user": email,
            "requestID": "action_1",
            "do": [{
                "remove": "all"
            }]
        }]
        path = f"/action/{self.orgId}"
        if test:
            parameter = {'testOnly':'true'}
        else:
            parameter = {}
        res = self.connector.postData(self.endpoint + path,params=parameter,data=message)
        return res