# -*- coding: utf-8 -*-

import re
from queue import Queue
from threading import Thread
import time

max_edit_distance = 3
verbose = 2
dictionary = {}
longest_word_length = 0
q = Queue(maxsize=0)
num_threads = 100
suggest_dict = {}
min_suggest_len = float('inf')
q_dictionary = {} 
string=""
def get_deletes_list(w):
    deletes = []
    queue = [w]
    for d in range(max_edit_distance):
        temp_queue = []
        for word in queue:
            if len(word)>1:
                for c in range(len(word)):  # character index
                    word_minus_c = word[:c] + word[c+1:]
                    if word_minus_c not in deletes:
                        deletes.append(word_minus_c)
                    if word_minus_c not in temp_queue:
                        temp_queue.append(word_minus_c)
        queue = temp_queue
    return deletes

def create_dictionary_entry(w,count=1):
    global longest_word_length
    new_real_word_added = False
    if w in dictionary:
        # increment count of word in corpus
        dictionary[w] = (dictionary[w][0], dictionary[w][1] + 1)  
    else:
        dictionary[w] = ([], count)  
        longest_word_length = max(longest_word_length, len(w))
        
    if dictionary[w][1]==count:
        new_real_word_added = True
        deletes = get_deletes_list(w)
        for item in deletes:
            if item in dictionary:
                # add (correct) word to delete's suggested correction list 
                dictionary[item][0].append(w)
            else:
                # note frequency of word in corpus is not incremented
                dictionary[item] = ([w], 0)  
        
    return new_real_word_added

def create_dictionary(fname):

    total_word_count = 0
    unique_word_count = 0
    
    with open(fname) as file:
        print ("Creating dictionary...")
        for line in file:
            # separate by words by non-alphabetical characters      
            line = line.split('\n')[0]
            words = re.findall('[a-z]+', line.lower())  
            count = line.split('\t')[1]
            for word in words:
                total_word_count += 1
                if create_dictionary_entry(word,int(count)):
                    unique_word_count += 1
    
    print(("total words processed: %i" % total_word_count))
    print(("total unique words in corpus: %i" % unique_word_count))
    return dictionary

def damerau_levenshtein_distance(s2, s1):
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in range(-1,lenstr2+1):
        d[(-1,j)] = j+1
 
    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 2
            d[(i,j)] = min(
                           d[(i-1,j)] + 0.5, # deletion
                           d[(i,j-1)] + 0.75, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                          )
            if i and j and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition
 
    return d[lenstr1-1,lenstr2-1]

def process_queue(q):
  while True:
        q_item = q.get()  # pop
        print (q_item)
        global suggest_dict, string, min_suggest_len

        if ((verbose<2) and (len(suggest_dict)>0) and 
              ((len(string)-len(q_item))>min_suggest_len)):
            break
        # process queue item
        if (q_item in dictionary) and (q_item not in suggest_dict):
            if (dictionary[q_item][1]>0):
                assert len(string)>=len(q_item)
                suggest_dict[q_item] = (dictionary[q_item][1], len(string) - len(q_item))
                # early exit
                if ((verbose<2) and (len(string)==len(q_item))):
                    break
                elif (len(string) - len(q_item)) < min_suggest_len:
                    min_suggest_len = len(string) - len(q_item)

            for sc_item in dictionary[q_item][0]:
                if (sc_item not in suggest_dict):
                    assert len(sc_item)>len(q_item)
                    assert len(q_item)<=len(string)
                    if len(q_item)==len(string):
                        assert q_item==string
                        item_dist = len(sc_item) - len(q_item)

                    assert sc_item!=string
                    item_dist = damerau_levenshtein_distance(sc_item, string)
                    if ((verbose<2) and (item_dist>min_suggest_len)):
                        pass
                    elif item_dist<=max_edit_distance:
                        assert sc_item in dictionary                    
                        suggest_dict[sc_item] = (dictionary[sc_item][1], item_dist)
                        if item_dist < min_suggest_len:
                            min_suggest_len = item_dist
                    if verbose<2:
                        suggest_dict = {k:v for k, v in list(suggest_dict.items()) if v[1]<=min_suggest_len}
       
        assert len(string)>=len(q_item)
        if ((verbose<2) and ((len(string)-len(q_item))>min_suggest_len)):
            pass
        elif (len(string)-len(q_item))<max_edit_distance and len(q_item)>1:
            for c in range(len(q_item)):    
                word_minus_c = q_item[:c] + q_item[c+1:]
                if word_minus_c not in q_dictionary:
                    q.put(word_minus_c)
                    q_dictionary[word_minus_c] = None  
        q.task_done()

def get_suggestions(searchStr, silent=False):
    if not bool(dictionary):
        init()
    start_time = time.time()
    global suggest_dict,string,q_dictionary
    suggest_dict = {}
    string=searchStr
    q_dictionary = {} 
    for i in range(num_threads):
        worker = Thread(target=process_queue, args=(q,))
        worker.setDaemon(True)
        worker.start()
    q.put(string)
    q.join()

    if (len(string) - longest_word_length) > max_edit_distance:
        if not silent:
            print ("no items in dictionary within maximum edit distance")
        return []

    if not silent and verbose!=0:
        print(("number of possible corrections: %i" %len(suggest_dict)))
        print(("  edit distance for deletions: %i" % max_edit_distance))
    
    as_list = list(suggest_dict.items())

    outlist = sorted(as_list, key=lambda term_freq_dist: (term_freq_dist[1][1], -term_freq_dist[1][0]))
    outlist = [term_freq_dist1[0] for term_freq_dist1 in outlist]
    
    run_time = time.time() - start_time
    print ('-----')
    print(('%.2f seconds to run' % run_time))
    print ('-----')
    
    if verbose==0:
        return outlist[0]
    else:
        return outlist[:25]


def best_word(s, silent=False):
    try:
        return get_suggestions(s, silent)[0]
    except:
        return None
    
def correct_document(fname, printlist=True):
    # correct an entire document
    with open(fname) as file:
        doc_word_count = 0
        corrected_word_count = 0
        unknown_word_count = 0
        print ("Finding misspelled words in your document...")
        
        for i, line in enumerate(file):
            # separate by words by non-alphabetical characters      
            doc_words = re.findall('[a-z]+', line.lower())  
            for doc_word in doc_words:
                doc_word_count += 1
                suggestion = best_word(doc_word, silent=True)
                if suggestion is None:
                    if printlist:
                        print(("In line %i, the word < %s > was not found (no suggested correction)" % (i, doc_word)))
                    unknown_word_count += 1
                elif suggestion[0]!=doc_word:
                    if printlist:
                        print(("In line %i, %s: suggested correction is < %s >" % (i, doc_word, suggestion[0])))
                    corrected_word_count += 1

    return

## main
def init():
    print ("Please wait...")
    try:
        create_dictionary("word_search.tsv")
    except:
        create_dictionary("testdata/big.txt")
    
    print (" ")
    print ("Word correction")
    print ("---------------")