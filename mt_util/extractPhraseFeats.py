#!/usr/bin/env python

"""
Extracts features from a Moses Phrase table

Author : Gaurav Kumar (Johns Hopkins University)
"""

import gzip
import argparse
import math
import codecs
import sys

parser = argparse.ArgumentParser("Extracts features from a Moses phrase table")
parser.add_argument("-p", "--phrase-table", dest="phraseTable", help="The location of the phrase table")
parser.add_argument("-o", "--out-feats", dest="outFeats", help="The location of the output file for the features")
opts = parser.parse_args()

if opts.phraseTable is None or opts.outFeats is None:
  parser.print_help()
  sys.exit(1)

phraseTable = gzip.open(opts.phraseTable)
outFeats = open(opts.outFeats, "w+")

outFeatsList = []
totalSourcePhraseCounts = 0

def processPhrase(phrase, details):
  '''
  Features : 
  1. Count feature
  2. Phrase unigram probability
  3. Length normalized phrase unigram probability
  4. Phrase translation Entropy
  5. Lexical translation Entropy
  '''
  global totalSourcePhraseCounts

  # Target, Source, Joint
  counts = details[0][2].strip().split()
  counts = [int(count) for count in counts]
  # The phrase count feature is always set to 1, this is for phrase counting
  countFeat = 1
  lenFeat = len(phrase.split())
  # The LM probabiliy should be in the log semiring (-ve log weights, lower is better)
  # This switch is made later, after the counts are normalized
  unnormalizedPhraseUnigram = math.log(counts[1])
  totalSourcePhraseCounts += counts[1]
  unnormalizedphraseUnigramLen = 1./lenFeat * unnormalizedPhraseUnigram
  # Phrase table probabilities are in real space
  phraseScores = [float(item[0].strip().split()[2]) for item in details]
  lexScores = [float(item[0].strip().split()[3]) for item in details]
  # normalize lex scores
  lexScores = [x / sum(lexScores) for x in lexScores]
  # Calculate entropies, lower is better
  phraseEntropy = sum([-1. * x * math.log(x, 2) for x in phraseScores])
  lexEntropy = sum([-1. * x * math.log(x, 2) for x in lexScores])
  # Lenfeat is sent out for use in normalization later
  outFeatsList.append(([phrase, countFeat, unnormalizedPhraseUnigram, unnormalizedphraseUnigramLen, phraseEntropy, lexEntropy], lenFeat))


def normalizeCountFeats():
  for feats, lenFeat in outFeatsList:
    feats[2] = feats[2] - math.log(totalSourcePhraseCounts)
    feats[3] = feats[3] - 1./lenFeat * math.log(totalSourcePhraseCounts)
    # Switch to using negative log probs, lower is better
    feats[2] = -1. * feats[2]
    feats[3] = -1. * feats[3]


def writeFeats():
  for feats, _ in outFeatsList:
    strFeats = [str(x) for x in feats]
    outFeats.write("\t".join(strFeats) + "\n")


# Get the source side phrases from the phrase table
currentSourcePhrase = ""
currentPhraseDetails = []
for line in phraseTable:
  # Split phrase pair
  phraseInfo = line.split("|||")
  sourcePhrase = phraseInfo[0].strip()
  if sourcePhrase == currentSourcePhrase:
    # Store details
    currentPhraseDetails.append(phraseInfo[2:])
  else:
    # First process the previous phrase
    if currentSourcePhrase != "":
      processPhrase(currentSourcePhrase, currentPhraseDetails)
    # Reset variables
    currentSourcePhrase = sourcePhrase
    currentPhraseDetails = [phraseInfo[2:]]

normalizeCountFeats()
writeFeats()

phraseTable.close()
outFeats.close()
