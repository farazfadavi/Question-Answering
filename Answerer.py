#!/usr/bin/env python

from ClueParser import ClueParser
import itertools as it
import re
import sys


name_finder = '<[^>|L]+>([^<]+)<\/[^>]+>'
class Answerer:

    def answer(self, parsed_clues):
        """Answer each clue and return a list of answers."""
        answers = []
        wiki_filename = "data/wiki-text-ner.txt"
        for parsed_clue in parsed_clues:
            clue_type, clue_entity = parsed_clue.split(":")
            if clue_type == "born_in":
                match, i = self.searchForPatterns(["born_in" + clue_entity, '<LOCATION>(Manhattan|Moscow)<\/LOCATION>', '<LOCATION>([^<]+)<\/LOCATION>, <LOCATION>([^<]+)<\/LOCATION>'], [0, 0], wiki_filename)
                if match is None or i == 0 or 'str' not in str(type(match)):
                    answers.append("No answer.")
                else:
                    answers.append("What is " + match + "?")
            else:
                match, i = self.searchForPatterns([clue_entity, 'born [\w+\s]+,\s([0-9]{4})', '(,|\))\s\(?([0-9]{4})', clue_entity + '<\/PERSON>\s\([A-Za-z]+\s[0-9]+,?\s([0-9]+)', 'born(\sin)?(\s[A-Za-z]+\s[0-9]+,?)?\s([0-9]+)'], [1, 2, 1, 3], wiki_filename)
                if match is None or i == 0 or 'str' not in str(type(match)):
                    answers.append("No answer.")
                else:
                    answers.append("What is " + match + "?")
        return answers

    def find_str(self, s, char):
        index = 0
        if char in s:
            c = char[0]
            for ch in s:
                if ch == c:
                    if s[index:index+len(char)] == char:
                        return index
                index += 1
        return -1

    def searchForPatterns(self, pattern_strings, pattern_positions, filename):
        """Searches a text file using several regular expressions at the same time, and returns one match. If more than
            one regular expression matches a piece of the file, the order of the regular expressions in the list
            is used to decide which match to return, so you should place more precise regular expressions earlier
            in the list. If more than one piece of the file matches the same regular expression, the last match
            in the file will be returned.

            patternStrings should be a list of regular experessions, ordered from most precise to least precise.

            patternPositions should be a list of integers of the same length as the list of regular expressions. and
            should indicate which group within each regular expression should be returned. Group 0 contains the entire
            match, group 1 contains the piece of the match inside first set of parantheses of the regular expression,
            group 2 contains the piece inside the second set of parentheses, etc.

            For example, for the regular expression "He was (maybe|probably) born in (\\d\\d\\d\\d)" and a file with
            the line "He was maybe born in 1899, and died in 1867.", these will be the groups you can choose from:
            - Group 0: "He was maybe born in 1899"
            - Group 1: "maybe"
            - Group 2: "1899"

            So if "1899" is the string that you want to include in your Jeopardy answer, you set the entry in patternPositions
            corresponding to this regular exrpession to 2.

            filename should be the filename for the text file being searched."""
        patterns = []
        clue_entity = pattern_strings[0]
        born = False
        if "born_in" in clue_entity:
            clue_entity = clue_entity.replace('born_in', '')
            born = True
        del pattern_strings[0]
        for pattern_string in pattern_strings:
            patterns.append(re.compile(pattern_string, re.IGNORECASE))

        # Iterate over the lines of the file.
        lines = loadList(filename)
        matched_groups = {}
        count = 0
        found = False
        foundInLine = 0
        for line in lines:
            if "<TITLE>" in line:
                count = 0
                title = re.findall(name_finder, line)
                if " ".join(title) == clue_entity:
                    found = True
                    count += 10# increases confidence in result
            if clue_entity in line:
                foundInLine = 1
            stop = False
            for i, p in enumerate(patterns):
                m = re.findall(p, line)
                if len(m) != 0:
                    for match in m:
                        query = match
                        if i != 0 and not born:
                            for each in match:
                                if len(each) == 4:
                                    match = each
                                    query = match
                        if born:
                            if len(match) == 2:
                                query = "<LOCATION>" + match[0]
                                match = match[0] + ", " + match[1]
                            else:
                                query = "<LOCATION>" + match
                        if self.find_str(line, clue_entity) != -1:
                            if self.find_str(line, query) > self.find_str(line, clue_entity):
                                count += foundInLine
                                if ("where" in line and "born" in line) or "was born in" in line:
                                    count += 2
                                foundInLine = -1
                        else:
                            count += foundInLine
                            foundInLine = -1
                        matched_groups[count] = match
                        if foundInLine == -1:
                            count = 0
                            foundInLine = 0
                        if found is True:# favors the very first occurence of the topic for a found file
                            found = False
                            count -= 10
        # Return the match corresponding to the first regular expression in the
        # list.
        if len(matched_groups) > 0:
            index = max(matched_groups.keys())
            returnVal = matched_groups[index]
            return returnVal, index
        else:
            return None

    def evaluate(self, guessed_answers, guessed_answers_from_parses, gold_answers):
        """Shows you how your model will score on the training/development data."""
        print "Guessed answers from clues:"
        score1 = self.evaluateAnswerSet(guessed_answers, gold_answers)
        print "Guessed answers from gold parses:"
        score2 = self.evaluateAnswerSet(
            guessed_answers_from_parses, gold_answers)
        print "Total score: {0}".format(score1 + score2)

    def evaluateAnswerSet(self, guessed_answers, gold_answers):
        """Scores one set of answers."""
        correct = 0
        wrong = 0
        no_answers = 0
        score = 0

        for guessed_answer, gold_answer_line in it.izip(guessed_answers, gold_answers):
            example_wrong = True  # guilty until proven innocent
            if guessed_answer == "No answer.":
                example_wrong = False
                no_answers += 1
            else:
                golds = gold_answer_line.split("|")
                for gold in golds:
                    if guessed_answer == gold:
                        correct += 1
                        score += 1
                        example_wrong = False
                        break
            if example_wrong:
                wrong += 1
                score -= 0.5
        print "Correct Answers: {0}".format(correct)
        print "No Answers: {0}".format(no_answers)
        print "Wrong Answers: {0}".format(wrong)
        print "Score: {0}".format(score)

        return score


def loadList(file_name):
    """Loads text files as lists of lines. Used in evaluation."""
    with open(file_name) as f:
        l = [line.strip() for line in f]
    return l


def main():
    """Tests the model on the command line. This won't be called in
        scoring, so if you change anything here it should only be code
        that you use in testing the behavior of the model."""
    clues_file = "data/part2-clues.txt"
    parses_file = "data/part2-parses.txt"
    gold_file = "data/part2-gold.txt"

    clues_val_file = "data/part2-clues-val.txt"
    parses_val_file = "data/part2-parses-val.txt"
    gold_val_file = "data/part2-gold-val.txt"

    training_clues_file = "data/part1-clues.txt"
    training_parsed_clues_file = "data/part1-parsedclues.txt"

    a = Answerer()

    # Test on unparsed questions.
    clues = loadList(clues_file)
    training_clues = loadList(training_clues_file)
    training_parsed_clues = loadList(training_parsed_clues_file)

    cp = ClueParser()
    cp.train(training_clues, training_parsed_clues)
    guessed_parses = cp.parseClues(clues)
    guessed_answers = a.answer(guessed_parses)
    # Test on parsed questions.
    gold_parses = loadList(parses_file)
    guessed_answers_from_parses = a.answer(gold_parses)

    # Evaluate both sets of answers.
    gold_answers = loadList(gold_file)
    a.evaluate(guessed_answers, guessed_answers_from_parses, gold_answers)

    validation_flag = False
    if len(sys.argv) > 1 and sys.argv[1] == '-v':
        print "\nValidation results:"
        clues_val = loadList(clues_val_file)
        guessed_parses_val = cp.parseClues(clues_val)
        guessed_answers_val = a.answer(guessed_parses_val)
        # Test on parsed questions.
        gold_parses_val = loadList(parses_val_file)
        guessed_answers_val_from_parses = a.answer(gold_parses_val)

        # Evaluate both sets of answers.
        gold_answers_val = loadList(gold_val_file)
        a.evaluate(guessed_answers_val,
                   guessed_answers_val_from_parses, gold_answers_val)


if __name__ == '__main__':
    main()
