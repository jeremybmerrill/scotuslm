##scotuslm
==========

####Trigram language model + Supreme Court opinions = lulzy fake opinions

My goal here is to combine the power of a trigram language model (simple machine learning to generate new text from old text) with the corpus of Supreme Court decisions. Eventually, I'd like to put together some semi-coherent opinions about arbitrary topics.

There are a couple of unorganized components to this barely-started project:
- scotus.py: Grab a few years of Supreme Court PDFs from the Supreme Court site by scraping the index page.
- textifier.rb: Turn those PDFs into txt files using [docsplit](http://github.com/documentcloud/docsplit).
- opinionifier.rb: Turn those txt files into distinct opinions with headers, footers stripped out, with each sentence on its own line.
- lm.rb: use trigram language model to generate sentences from the given opinions.

####Usage notes:
The lm.rb file allows a trigram language model (where the next word is chosen randomly from all of those that have occurred in the training set after the previous two (known) words) to be trivially implemented over any set of data. 

There are only two necessary methods.
1. LanguageModel.new
    - Specify a list of filepaths to train on and, optionally, a lambda to apply to that list. Only the filenames on which the lambda returns true will be used for training. (For instance, if you glob everything in a folder, you might only want the ones that include the word "SCALIA")
2. #getPhrase: returns a sentence generated from the language model. Options:
    - :maxLen, default 30. The maximum length of a sentence. Often good to set, in case sentence ends up in a loop.
    - :unpathiness, default 0. How often to back off to bigrams (only the last known word determines probabilities of following word)
    - :wordTwoBack, default "". Start the sentence with this word. Definitely a good idea to set wordBack too, if you set this.
    - :wordBack, default "". Start the sentence with this word.
    - :debug, default false. Print debug messages. Quite verbose.
    - :engtagger, default false. Count verbs and complementizers (e.g. which, that) to try to get more coherent sentences. Definitely a work in progress.
    - :guaranteeParse, default false. Reject sentences that the CMU LinkParser can't parse.

####TODO:
Lots of things!
- Topics
- Find a way to make sentences more coherent.
- Attempt to write more coherent sentences by counting complementizers (which, that) and verbs to ensure verbs = complementizers +1. This gives the model a bit of "long distance" reasoning to prevent ungrammatical output like "The people that the supreme court" or "The petitioner who files the brief"

####Known Issues:
- Everything!
- Opinions still have some cruft in them that needs to be cleaned.

####Supreme Court Corpus:
This project includes (in txts/ and opinions/) raw pdftotext output and cleaned plaintext of all 2009, 2010 and 2011 term US Supreme Court opinions. They're not guaranteed to be perfect, though they should be getting better. Please use this corpus, if you'd like.