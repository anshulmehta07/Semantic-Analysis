#!/usr/bin/env python
# coding: utf-8

# #### Semantic Analysis of Luxembourg based Companies

# In[39]:


# Import necessary packages
import os                               # Package to list files in directory
import re                               # Package for regular expressions
import csv                              # Package to write to CSV files
import spacy                            # NLP package
from collections import Counter         # Get word frequency
from spacy import displacy              # For visual relation of tokens in a sentence
from spacy.matcher import Matcher       # For identifying tags


# In[62]:


all_files = os.listdir("PwC Data/1/") #Get a list of all files in the current directory
len(all_files)


# In[63]:


# Prepare master output CSV file and write headers
with open('output.csv', 'w', newline='', encoding = 'utf-8') as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["Numero_RCS", "Publication", "Date", "Company_Name", "Address", "Tags", "Employee_List"])    
output_file.close()

# Prepare corporate object CSV file for training tags
with open('corp_obj.csv', 'w', newline='', encoding = 'utf-8') as output_file_1:
    writer = csv.writer(output_file_1)
    writer.writerow(["Detailed_Corporate_Objective"])    
output_file_1.close()

# Prepare exception txt file
with open('expections.txt', 'w', newline='\n') as exception_file:
    exception_file.write("::EXCEPTION FILES LIST::")
exception_file.close()

# Read all files in directory
for each_file in all_files:
    with open("PwC Data/1/"+ each_file, encoding = 'utf-8') as file: #utf-8 encoding to support accents
        file_contents = file.read()
        #print(file_contents)
        print("Processing file:", each_file)
        extract_information(each_file)
    file.close()

# Call this function to identify the tags to train for nlp_module function
# Uncomment to reidentify tags for newer corporate objects
nlp_trainer()         


# In[49]:


#############################################################################################################
#                                          EXTRACTION FUNCTION                                              #
#############################################################################################################

# This function is used to extract information such as the primary key (numero _RCS), publication number, 
# date of publication, company name, address & corporate object using regular expressions.

def extract_information(each_file):
    # Extract Numero RCS
    if re.search(r'Numéro RCS :\s+(.*)', file_contents):                                     # Check primary key
        numero_rcs = re.search(r'Numéro RCS :\s+(.*)', file_contents).group(1)               # Get Numero RCS
    else:
        exceptions(each_file)                                                                # Move files without key to exception
        return 0;                                                                            
    
    # Extract publication number
    if re.search(r'Référence de publication :\s+(.*)', file_contents):
        publication = re.search(r'Référence de publication :\s+(.*)', file_contents).group(1)# Get Publication number
    elif re.search(r'RESA\_\d\d\d\d\_\d\d\d', file_contents):
        publication = re.search(r'RESA\_\d\d\d\d\_\d\d\d', file_contents).group()
    else:
        publication = "NA"
        
    date = ""; company_name = "";                                                            # Initialize variables
    
    # Extract date, company name, & address
    if re.search('Déposé.*le ((.*\n){1,10})', file_contents):
        company_info = re.search('Déposé.*le ((.*\n){1,10})', file_contents).group(1)        # Get company information
        date = company_info[0:10]                                                            # Get date
        company_info_1 = company_info[11:].strip()
        company_name = company_info_1.split('\n')[0]                                         # Get company name
        company_address = company_info_1.split(company_name)[1]                              # Get company address
        if re.search(r'Siège social.*:((.*\n){1,3})', company_info):
            address = re.search(r'Siège social.*:((.*\n){1,3})', company_info).group(1)
            address = address.replace('\n',' ')
        elif re.search(r'\d.*|L-.*',company_address):
            address = company_address.replace('\n',' ')
            address = re.search(r'\d.*|L-.*',address).group()
        else:
            address = ""
        if re.search(r'((.*)) CON|STATUTS|GESEL|ASSEMBLEE|EX|NUM',address,re.IGNORECASE):   # Remove trailing words from address    
            address = re.search(r'((.*)) CON|STATUTS|GESEL|ASSEMBLEE|EX|NUM',address, re.IGNORECASE).group(1)
    else:
        company_info = ""
    
    # Extract corporate object
    if re.search(r'art.*\d.*object((.*\n){1,10})', file_contents, re.IGNORECASE):           
        corporate_obj = re.search(r'art.*\d.*object((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    elif re.search(r'^\d.*object((.*\n){1,10})', file_contents, re.IGNORECASE):
        corporate_obj = re.search(r'art.*\d.*object((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    elif re.search(r'art.*\d.*purpose((.*\n){1,10})', file_contents, re.IGNORECASE):
        corporate_obj = re.search(r'art.*\d.*purpose((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    elif re.search(r'^\d.*purpose((.*\n){1,10})', file_contents, re.IGNORECASE):
        corporate_obj = re.search(r'\d.*purpose((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    elif re.search(r'art.*\d.*obj((.*\n){1,10})', file_contents, re.IGNORECASE):
        corporate_obj = re.search(r'art.*\d.*obj((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    elif re.search(r'art.*\d.*Gegenstand((.*\n){1,10})', file_contents, re.IGNORECASE):
        corporate_obj = re.search(r'art.*\d.*Gegenstand((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    # some results might be inaccurate with the below regex, but it greatly improves the output matches
    # comment below regex block if required
    elif re.search(r'objet social((.*\n){1,10})', file_contents, re.IGNORECASE):     
        corporate_obj = re.search(r'objet social((.*\n){1,10})', file_contents, re.IGNORECASE).group(1)
        corporate_obj = corporate_obj.replace('\n',' ')
    else:
        corporate_obj = ""
    
    # Extract employee name 
    if re.findall(r'Monsieur\s(.+?),|Madame\s(.+?),',file_contents):
        employees_m = re.findall(r'Monsieur\s(.+?),',file_contents)
        employees_f = re.findall(r'Madame\s+(.+?),',file_contents)
        employees = employees_m + employees_f
    elif re.findall(r'Mr.\s(.+?),|Mrs.\s(.+?),',file_contents):
        employees_m = re.findall(r'Mr.\s(.+?),',file_contents)
        employees_f = re.findall(r'Mrs.\s+(.+?),',file_contents)
        employees = employees_m + employees_f
    else:
        employees = ""
    if employees != "":
        employees = list(dict.fromkeys(employees))                                          # Remove duplicates
        employees = str(employees)[1:-1]                                                    # Convert list to strings
    
    # Calls NLP module to extract tokens from corporate object & return a list of tags 
    tags = nlp_module(corporate_obj)
    if tags !=[]:
        tags = str(tags)[1:-1]
    else:
        tags = ""
    
    # Write files
    if company_name == "":                                                                  # Move file with no name to exception
        exceptions(each_file)
    else:
        with open('output.csv', 'a', newline='', encoding = 'utf-8') as output_file:        # Append to CSV file
            writer = csv.writer(output_file)
            writer.writerow([numero_rcs, publication, date, company_name, address, tags, employees])
        output_file.close()
        
        with open('corp_obj.csv', 'a', newline='', encoding = 'utf-8') as output_file_1:     # Append to CSV file
            writer = csv.writer(output_file_1)
            writer.writerow([corporate_obj])
        output_file_1.close()


# In[58]:


#############################################################################################################
#                                               NLP FUNCTION                                                #
#############################################################################################################

# This function is used to extract key tags from the corporate onbective of companies to help identify the 
# key functionality & type of company

def nlp_module(corporate_obj):
    #nlp_en = spacy.load('en_core_web_sm')   Run this command if link to model is working
    #nlp_de = spacy.load('de_core_news_sm')  Run this command if link to model is working
    #nlp_fr = spacy.load('fr_core_news_sm')  Run this command if link to model is working
    
    nlp = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/en_core_web_sm/en_core_web_sm-2.0.0')
    #nlp_de = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/de_core_news_sm/de_core_news_sm-2.0.0')
    #nlp_fr = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/fr_core_news_sm/fr_core_news_sm-2.0.0')
    
    matcher = Matcher(nlp.vocab)
    complete_doc_en = nlp(corporate_obj)
    
    tags = []

    # Add match ID with no callback
    matcher.add("Acquisition", None, [{"LEMMA": "acquire"}],
                                     [{"LEMMA": "acquisition"}],
                                     [{"LEMMA": "l’acquisition"}])

    matcher.add("Investment", None, [{"LEMMA": "invest"}],
                                    [{"LEMMA": "investment"}],
                                    [{"LEMMA": "investissement"}])

    matcher.add("Holding", None, [{"LEMMA": "holds"}],
                                 [{"LEMMA": "holding"}])
    
    matcher.add("Development", None, [{"LEMMA": "développer"}],
                                     [{"LEMMA": "development"}],
                                     [{"LEMMA": "développement"}])
    
    matcher.add("Real Estate", None, [{"LEMMA": "immeubles"}],
                                     [{"LEMMA": "immobilières"}],
                                     [{"LEMMA": "immobiliers"}],
                                     [{"LEMMA": "property"}])

    matcher.add("Administration", None, [{"LEMMA": "administration"}],
                                        [{"LEMMA": "l’administration"}])

    matcher.add("Purchase", None, [{"LEMMA": "l'achat"}],
                                  [{"LEMMA": "achat"}],
                                  [{"LEMMA": "purchase"}])
                
    matcher.add("Subscription", None, [{"LEMMA": "souscription"}],
                                      [{"LEMMA": "subscription"}])
                            
    matcher.add("Exchange", None, [{"LEMMA": "exchange"}],
                                  [{"LEMMA": "échange"}])
                
    matcher.add("Foreign", None, [{"LEMMA": "foreign"}],
                                 [{"LEMMA": "étrangères"}],
                                 [{"LEMMA": "l’étranger"}])
 
    matcher.add("Management", None, [{"LEMMA": "gestion"}],
                                     [{"LEMMA": "management"}])
    
    matcher.add("Shares", None, [{"LEMMA": "shares"}],
                                [{"LEMMA": "actions"}])

    matcher.add("Bonds", None, [{"LEMMA": "bonds"}],
                               [{"LEMMA": "obligations"}])
    
    matcher.add("Debentures", None, [{"LEMMA": "debenture"}])
    
    matcher.add("Debt", None, [{"LEMMA": "debt"}],
                              [{"LEMMA": "dette"}],
                              [{"LEMMA": "créances"}])
    
    matcher.add("Securities", None, [{"LEMMA": "titres"}],
                                    [{"LEMMA": "securities"}])
    
    matcher.add("Commercial", None, [{"LEMMA": "commercial"}],
                                    [{"LEMMA": "commerciales"}],
                                    [{"LEMMA": "commerciale"}])
    
    matcher.add("Finance", None, [{"LEMMA": "finance"}],
                                 [{"LEMMA": "financiers"}],
                                 [{"LEMMA": "financial"}])
    
    matches = matcher(complete_doc_en)
    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]  # Get string representation
        span = complete_doc_en[start:end]  # The matched span
        #print(string_id, span.text)
        tags.append(string_id)

    tags = list(dict.fromkeys(tags))
    return tags


# In[44]:


#############################################################################################################
#                                            EXCEPTION FUNCTION                                             #
#############################################################################################################

# This function is used to write all files without a primary key or without an identifyable company name 
# into an exception text file for manual processing

def exceptions(each_file):
    with open('expections.txt', 'a', newline='\n', encoding = 'utf-8') as exception_file:     # Append to Exception file
            exception_file.write('\n')
            exception_file.write(each_file)
    exception_file.close()


# In[47]:


#############################################################################################################
#                                       NLP TRAINER FUNCTION                                                #
#############################################################################################################

# This function is used to identify the key tags from the coporate objects data extracted from the input file
# These identified tags are used in the nlp_module function. Run this function everytime there are newer 
# corporate objects that have been added into the input file

def nlp_trainer():
    
    # Load NLP modules
    #nlp_en = spacy.load('en_core_web_sm')  Run this command if link to model is working
    #nlp_de = spacy.load('de_core_news_sm') Run this command if link to model is working
    #nlp_fr = spacy.load('fr_core_news_sm') Run this command if link to model is working
    nlp = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/en_core_web_sm/en_core_web_sm-2.0.0')
    nlp_de = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/de_core_news_sm/de_core_news_sm-2.0.0')
    nlp_fr = spacy.load('C:/Users/swaya/Anaconda3/Lib/site-packages/fr_core_news_sm/fr_core_news_sm-2.0.0')
    
    # File containing corporate objects of all companies.
    with open("corp_obj.csv", encoding = 'utf-8') as file:
        file_contents = file.read()
        #print(file_contents)
    file.close()
    
    # Uncomment to display links between tokens in a 'sample' sentence
    # displacy.serve(nlp(sample), style='dep')
    
    
    ## English model
    complete_doc_en = nlp(file_contents)
    
    # Select English noun chunks
    text_en = ""
    for token in complete_doc_en.noun_chunks:
        text_en = text_en + token.text + ' '
    text_noun_en = nlp(text_en)

    # Remove stop words and punctuation symbols
    words = [token.text for token in text_noun_en
              if not token.is_stop and not token.is_punct]

    # Get 150 most frequent nouns to identify tags (includes French & German non-nouns)
    word_freq = Counter(words)
    common_words_en = word_freq.most_common(150)
    print("\n::150 most frequent English noun tokens::\n")
    print(common_words_en)
    
    
    ## French model
    complete_doc_fr = nlp_fr(file_contents)

    #Select French noun chunks
    text_fr = ""
    for token in complete_doc_fr.noun_chunks:
        text_fr = text_fr + token.text + ' '
    text_noun_fr = nlp_fr(text_fr)

    # Remove stop words and punctuation symbols
    words = [token.text for token in text_noun_fr
              if not token.is_stop and not token.is_punct]
    
    # Get 150 most frequent nouns to identify tags (includes English & German non-nouns)
    word_freq = Counter(words)
    common_words_fr = word_freq.most_common(150)
    print("\n::150 most frequent French noun tokens::\n")
    print(common_words_fr)
    
    
    ## German model
    complete_doc_de = nlp_de(file_contents)

    #Select German noun chunks
    text_de = ""
    for token in complete_doc_de.noun_chunks:
        text_de = text_de + token.text + ' '

    text_noun_de = nlp_de(text_de)

    # Remove stop words and punctuation symbols
    words = [token.text for token in text_noun_de
              if not token.is_stop and not token.is_punct]
    
    # Get 150 most frequent nouns to identify tags (includes English & German non-nouns)
    word_freq = Counter(words)
    common_words_de = word_freq.most_common(150)    
    print("\n::150 most frequent German noun tokens::\n")
    print(common_words_de)
    
    # common_words_en, common_words_fr, & common_words_de are used to manually identify key tags 
    # from corporate_obj variable in nlp_module function and are grouped using matcher 

