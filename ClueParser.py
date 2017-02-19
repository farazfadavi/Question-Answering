#!/usr/bin/env python
# CS124 Homework 5 Jeopardy
# Original written in Java by Sam Bowman (sbowman@stanford.edu)
# Ported to Python by Milind Ganjoo (mganjoo@stanford.edu)

import itertools as it
from NaiveBayes import NaiveBayes
import re


entity_finder = '<[^>|L]+>([^<]+)<\/[^>]+>'
location_finder = '<[^>]+>([^<]+)<\/\w+>, <\w+>([^<]+)<\/[^>]+>'
capital_finder = '([A-Z]\w+)'
capital_remover = '([\s\S]*?)(<\/?[A-Z]+>|$)'
class ClueParser:
    def __init__(self):
        self.classifier = NaiveBayes()
        pass

    def findEntities(self, clue):
        entities = []
        matches = re.findall(location_finder, clue)
        for match in matches:
            location = match[0] + ", " + match[1]
            entities.append(location)
        matches = re.findall(entity_finder, clue)
        for match in matches:
            entities.append(match)
        return entities

    def findCapEntity(self, clue):
        matches = re.findall(capital_finder, clue)
        if len(matches) != 0:
            return " ".join(matches)
        else:
            return ""

    def parseClues(self, clues):
        """Parse each clue and return a list of parses, one for each clue."""
        parses = []
        for clue in clues:
            klass = self.classifier.classify(self.findFeatures(clue))
            entities = self.findEntities(clue)
            parse = klass + ":"
            if len(entities) != 0:
                parse += entities[-1]
            else:
                parse += self.findCapEntity(clue)
            parses.append(parse)
        return parses

    def findFeatures(self, clue):
        words = []
        start = 0
        i = 0
        # clue = clue.replace("<PERSON>", "")
        # clue = clue.replace("<LOCATION>", "")
        # clue = clue.replace("<ORGANIZATION>", "")
        # clue = clue.replace("</PERSON>", "")
        # clue = clue.replace("</LOCATION>", "")
        # clue = clue.replace("</ORGANIZATION>", "")
        matches = re.findall(capital_remover, clue)
        sent = []
        for match in matches:
            sent.append(match[0])
        clue = "".join(sent)
        while i < len(clue):
            if clue[i] == "<":
                print clue
            if (clue[i] == " " or i == len(clue) - 1) and i != start:
                word = clue[start:i]
                if word[0] == " ":
                    word = word[1:]
                words.append(word)
                start = i + 1
            i += 1
        return words

    def train(self, clues, parsed_clues):
        """Trains the model on clues paired with gold standard parses."""
        klasses = []
        for answer in parsed_clues:
            klass = answer[:answer.index(":")]
            klasses.append(klass)
        features = []
        for clue in clues:
            features.append(self.findFeatures(clue))
        self.classifier.addExamples(features, klasses)

    def evaluate(self, parsed_clues, gold_parsed_clues):
        """Shows how the ClueParser model will score on the training/development data."""
        correct_relations = 0
        correct_parses = 0
        for parsed_clue, gold_parsed_clue in it.izip(parsed_clues, gold_parsed_clues):
            split_parsed_clue = parsed_clue.split(":")
            split_gold_parsed_clue = gold_parsed_clue.split(":")
            if split_parsed_clue[0] == split_gold_parsed_clue[0]:
                correct_relations += 1
                if (split_parsed_clue[1] == split_gold_parsed_clue[1] or
                        split_parsed_clue[1] == "The " + split_gold_parsed_clue[1] or
                        split_parsed_clue[1] == "the " + split_gold_parsed_clue[1]):
                    correct_parses += 1
        print "Correct Relations: %d/%d" % (correct_relations, len(gold_parsed_clues))
        print "Correct Full Parses: %d/%d" % (correct_parses, len(gold_parsed_clues))
        print "Total Score: %d/%d" % (correct_relations + correct_parses, 2 * len(gold_parsed_clues))

def loadList(file_name):
    """Loads text files as lists of lines. Used in evaluation."""
    with open(file_name) as f:
        l = [line.strip() for line in f]
    return l

def main():
    """Tests the model on the command line. This won't be called in
        scoring, so if you change anything here it should only be code
        that you use in testing the behavior of the model."""

    clues_file = "data/part1-clues.txt"
    parsed_clues_file = "data/part1-parsedclues.txt"
    cp = ClueParser()

    clues = loadList(clues_file)
    gold_parsed_clues = loadList(parsed_clues_file)
    assert(len(clues) == len(gold_parsed_clues))

    cp.train(clues, gold_parsed_clues)
    parsed_clues = cp.parseClues(clues)
    cp.evaluate(parsed_clues, gold_parsed_clues)

if __name__ == '__main__':
    main()
