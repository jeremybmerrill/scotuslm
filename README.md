scotuslm
========

Trigram language model + Supreme Court opinions = lulzy fake opinions

My goal here is to combine the power of a trigram language model (simple machine learning to generate new text from old text) with the corpus of Supreme Court decisions. Eventually, I'd like to put together some semi-coherent opinions about arbitrary topics.

There are a couple of unorganized components to this barely-started project:
- scotus.py: Grab a few years of Supreme Court PDFs from the Supreme Court site by scraping the index page.
- textifier.rb: Turn those PDFs into txt files using [docsplit](http://github.com/documentcloud/docsplit).
- opinionifier.rb: Turn those txt files into distinct opinions with headers, footers stripped out.
- lm.rb: use trigram language model to generate sentences from the given opinions.

TODO:
Lots of things!
- Intelligently combine words that may have been broken at the end of a line. One piece of information lost in converting a PDF to text with poppler/pdftotext is what words have been split. Thus, I will build something to check for w1\nw2 whether w1w2 is a word, whether w1 and w2 are independent words, etc.
- Attempt to write more coherent sentences by counting complementizers (which, that) and verbs to ensure verbs = complementizers +1. This gives the model a bit of "long distance" reasoning to prevent ungrammatical output like "The people that the supreme court" or "The petitioner who files the brief"

Known Issues:
Everything!