#!/usr/bin/python 
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------
# Name:        buildict 
# Purpose:     Build arabic dictionnary for spelling from a wordlist 
# Author:      Taha Zerrouki (taha.zerrouki[at]gmail.com) 
# Created:     2015-03-25
#  Copyright:   (c) Taha Zerrouki 2015 
# Licence:     GPL 
#---------------------------------------------------------------------

"""
    Arabic spell checker dictionary build script 
"""
import sys
import re
import operator
from collections import Counter

sys.path.append("../../lib")
import tashaphyne.stemming 
import stem_const
LIMIT = 10000000
#LIMIT = 1000
#FILENAME = 'arabicwordlist.txt'
INPUT_FILENAME = '../data/Arabic-Wordlist-1.6/arabic-wordlist-1.6.txt'
OUTPUT_FILE_AFFIX = "../output/arabic.pat"
OUTPUT_FILE_WORDS = "../output/arabic.root" 
BASEDIGIT = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphabet = u'ذضصثقفغعهخحجدطكمنتالبيسشظزوةىرؤءئأإآ'

bigrams_dict ={}
def bialphabet(phrase):
    """
    Generate all possible bi grams from phrase
    @param phrase: the given alphabet
    @type phrase: unicode
    @return: list of bigrams
    @rtype: list of unicode
    """
    phrase = " "+phrase+" "
    bilist = []
    for a in phrase:
        for b in phrase:
           bilist.append("".join([a,b]))
    return bilist
bigrams_dict = dict((key,0) for key in bialphabet(alphabet))

def getbigrams(word):
    """
    extract all bigrams from the word with stats
    @param word: the given word
    @type word: unicode
    @return: dict of bigrams
    @rtype: dict of integer
    """
    text = " "+word+" "
    bigrams = Counter(x+y for x, y in zip(*[text[i:] for i in range(2)]))
    return bigrams

def updatebigrams(word):
    """
    update bigrams from the given word
    """
    #global bigrams_dict
    bilist = getbigrams(word)
    for bi in bilist:
        count = bilist.get(bi, 0)
        if bi in bigrams_dict:
            bigrams_dict[bi] += count

def basecode(number,  basedigit = BASEDIGIT):
    """
    create a string code for every affixes, as flags,
    every affix can have a code according to the number and the enumeration base used,
    the base digit can have letters small and capital,
    @param number: a given number
    @type number: integer
    @param basedigit: a list of symbole used by the given base
    @type basedigit: string
    @return: coded number in the given base
    @rtype: string
    """
    if number == 0: return "0"
    coded = []
    base = len(basedigit)
    while number !=0:
            coded.append(basedigit[number % base])
            number = number / base
    return "".join(reversed(coded))
def compact_list(lst):
    sublists =[]
    tmp = []
    for x in lst:
        if not tmp:
            tmp.append(x)
        elif tmp[len(tmp)-1] +1 == x :
            tmp.append(x)
        else:
            sublists.append(tmp)
            tmp = [x]
    if tmp:
        sublists.append(tmp)
    text = ""
    for l in sublists:
        if len(l) > 2:
            text  +=";%s-%s"%(basecode(l[0]), basecode(l.pop()))
        elif len(l) == 2:
             text += ";%s;%s"%(basecode(l[0]), basecode(l.pop()) )
        else:
             text += ";%s"%basecode(l[0])
    return text

 
def build_dict(inputfile = INPUT_FILENAME , 
                outfile_affix = OUTPUT_FILE_AFFIX,
                outfile_words = OUTPUT_FILE_WORDS  ):
    """
    Convert a large wordlist to a spellchecking dictionary
    @param inputfile: wordlist file name
    @type  inputfile: string
    @param outfile_affix: affix file name in csv format
    @type  outfile_affix: string
    @param outfile_words: words file name in csv format
    @type  outfile_words: string
    """
    stemmer = tashaphyne.stemming.ArabicLightStemmer()
    stemmer.set_prefix_list(stem_const.PREFIX_LIST);
    stemmer.set_suffix_list(stem_const.SUFFIX_LIST);
    worddict  = { }
    # the affix dict is initialized by generalized procletic Feh and WAW
    # the generalized procletic generalize and reduce dictionary size
    affixdict = {u"و":[], u"ف":[],  }
    line_nb = 1
    with  open(inputfile, "r+") as myfile :
        line = myfile.readline().decode('utf8')

        while line and line_nb< LIMIT:
            conjonction = False
            word = line.strip("\n").split(" ")[0]
            updatebigrams(word)
            # stemming the given word
            # extract waw and feh as a generic prefix with all possible words
            if word.startswith(u"ف") or word.startswith(u"و"):
                conjonction = word[0]
                word = word[1:]

            stemmer.segment(word)
            
            # extract the affix 
            #~ affix = u"-".join([stemmer.get_prefix(),stemmer.get_suffix()])
            stemmer.light_stem(word)
            affix = stemmer.get_starword()
            stem = stemmer.get_stem()
            if conjonction:
                affixdict[conjonction].append(stem)
            if affix in affixdict:
                affixdict[affix].append(stem)
            else:
                affixdict[affix] = [stem, ]
            line = myfile.readline().decode('utf8')
            line_nb += 1            
        # calculate stats for every affix 
        # the number of stems used this affix
        affixcount = [ (aff, len(affixdict[aff])) for aff in affixdict.keys()]
        # this stats used to compress affix flags
        # in order to give short flag to frequent aff
        # sort affix in reverse according to stats ( stems frequent)

        sorted_affix = sorted(affixcount, key=operator.itemgetter(1), reverse=True)

        # the dictionary of flags, 
        # each flag with the affix and frequency of this affix
        flagdict ={}
        # the flags are sequentiel numeric numbers
        counter = 1
        for aff, cnt in sorted_affix:
            #print (u"%s\t%d"%(aff, cnt)).encode('utf8')
            flag = counter
            #flag_str = str(hex(flag)).replace("0x",'')
            flag_str = basecode(flag)
            counter += 1
            flagdict[flag] = (aff, cnt)
            for stem in affixdict[aff]:
                # add the current flag to the dict entree as stem
                # like this 
                # stem/Flag => word/1
                if stem in worddict:
                    if not flag_str in worddict[stem]:
                        worddict[stem].append(flag_str)
                        #~ worddict[stem].append(flag)
                else: # if the stem doesn't exist add it
                    worddict[stem] = [flag_str, ]        
                    #~ worddict[stem] = [flag, ]        
        myfile.close()
        # print affix codes
        with  open(outfile_affix,"w+") as affix_file:
            print "------------affix dictionary--------------"
            for flag in flagdict:
                line = (u"%s\t%s\t%s\n"%(basecode(flag), flagdict[flag][0],flagdict[flag][1])).encode("utf8")
                affix_file.write(line)
            affix_file.close()

        #print word dictionary

        with  open(outfile_words,"w+") as dict_file:
            print "------------word dictionary--------------"
            for word in worddict:
                
                line = (u"%s\t%s\n"%(word, u";".join(worddict[word]))).encode("utf8")
                #~ line = (u"%s\t%s\n"%(word, compact_list(worddict[word]))).encode("utf8")
                dict_file.write(line)
            dict_file.close()
    return flagdict, worddict
        
def mainly():
    """
    main test
    """
    build_dict()
    
    print len(bigrams_dict)

    print "----bigrams----"
    for bi in bigrams_dict:
        print u";".join([bi,str(bigrams_dict[bi])]).encode('utf8') 
    print len(bigrams_dict), len(filter(lambda x: x, bigrams_dict.values()))
if __name__ == "__main__":
    mainly()
