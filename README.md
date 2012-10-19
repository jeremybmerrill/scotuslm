scotuslm
==========

####Trigram language model + Supreme Court opinions = lulzy fake opinions

My goal here is to combine the power of a trigram language model (simple machine learning to generate new text from old text) with the corpus of Supreme Court decisions. Eventually, I'd like to put together some semi-coherent opinions about arbitrary topics.

There are a couple of unorganized components to this barely-started project:
- scotus.py: Grab a few years of Supreme Court PDFs from the Supreme Court site by scraping the index page.
- textifier.rb: Turn those PDFs into txt files using [docsplit](http://github.com/documentcloud/docsplit).
- opinionifier.rb: Turn those txt files into distinct opinions with headers, footers stripped out, with each sentence on its own line.
- LanguageModel.py: Use a trigram language model to generate sentences from given input texts.
- TopicSimilarity.py: When trained, returns words similar to a given word using TFIDF and cosine-similarity across N-space for N = count(documents)
- lm.rb (deprecated): use trigram language model to generate sentences from the given opinions.

####Usage notes:
The LanguageModel module allows a trigram language model (where the next word is chosen randomly from all of those that have occurred in the training set after the previous two (known) words) to be trivially implemented over any set of data. 

There are only two necessary methods:

1. LanguageModel.new(listOfFilepaths, lambda={|a| a })

  - Specify a list of filepaths to train on and, optionally, a lambda to apply to that list. Only the filenames on which the lambda returns true will be used for training. (For instance, if you glob everything in a folder, you might only want the ones that include the word "SCALIA")

2. get_hrase(opts): returns a sentence generated from the language model. Options:

  - "maxLen, default 30. The maximum length of a sentence. Often good to set, in case sentence ends up in a loop.
  - "unpathiness", default 0. How often to back off to bigrams (only the last known word determines probabilities of following word)
  - "wordTwoBack", default "". Start the sentence with this word. Definitely a good idea to set wordBack too, if you set this.
  - "wordBack", default "". Start the sentence with this word.
  - "debug", default false. Print debug messages. Quite verbose.
  - "engtagger", default false. Count verbs and complementizers (e.g. which, that) to try to get more coherent sentences. Definitely a work in progress.
  - "guaranteeParse", default false. Reject sentences that the CMU LinkParser can't parse.

####Implementation notes:

#####Language model
TODO: write this bit.

This implements a backoff scheme which, I'm told, resembles "Stupid Backoff" from _cite_. I call this backoff scheme the "Jeremy left his Jurafsky/Martin five states away" backoff.
Smarter capitalization (downcase everything but proper nouns, i.e. things not in the wordlist that arrive capitalized.)

#####TopicSimilarity
This should really be called WordSimilarity. #TODO
Returns words and their similarity to a given word. Each word is represented by a vector of TFIDFs per document. A word is more similar to the given word if the cosign difference between their vectors is lower.

####TODO:
Lots of things!
- Improve very shallow parsing.
- Improve backoff. "Stupid backoff", smoothing (Keyser-Ney?)
- Experiment with TFIDF variants in similarity.
- Tokenize on words and punctuation (treating punctuation like a word)
- Re-sentence-tokenize the opinions using NLTK.
- Find a simple NLTK parser in order to guarantee parseable output.
- Split the LanguageModel module into just an LM and separate text-generation module.
- Topics: allow multiple topics to be set, e.g. a document-level topic and a paragraph level topic (so a paragraph that involves habeas will involve habeas, even if the document is about federalism.)
- Know about paragraphs.
- LanguageModel on phrases? Structure?
- LanguageModel indexes on a combo of word and POS? So "REFuse" and "reFUSE" are diff words. (tuples are hashable.)
(Language model on parts of speech; once a structure is generated, fill it in with words based on frequency, previous words, topic, etc.)


####Known Issues:
- Everything!
- Opinions still have some cruft in them that needs to be cleaned.

####Supreme Court Corpus:
This project includes (in txts/ and opinions/) raw pdftotext output and cleaned plaintext of all 2009, 2010 and 2011 term US Supreme Court opinions. They're not guaranteed to be perfect, though they should be getting better. Please use this corpus, if you'd like.