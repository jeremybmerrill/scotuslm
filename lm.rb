# encoding: utf-8 
require 'engtagger'
require 'nokogiri'

class LanguageModel
=begin
What's the best model for a 3LM?

threelm[word_two_back][word_back]
=> {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
=> {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

"backoff" -- if count is less than <10, go to 2LM

=end

  def initialize(pathglob,lambdaFunc = lambda{|a| a } )
    trigram_counts = {}
    unigram_counts = {}
    unigram_counts.default = 0

    bigram_counts_member = {}
    bigram_counts_member.default = 0
    bigram_counts = {} #e.g. {San => {Francisco => 50, Jose => 20} }
    bigram_counts.default = bigram_counts_member

    trigram_counts_member = {}
    trigram_counts_member.default = bigram_counts_member
    trigram_counts.default = trigram_counts_member

    @engtagger = EngTagger.new
    #@complementizer_list = ['AZ', 'TH', 'TS', ]
    #@verb_list = ['S']
    @complementizer_list = ["wp", "wps," "wdt", "wrb"] #also, "in", dealt with separately
    @actual_IN_complementizers = ["that", "although", "after", "although", "if", "unless", "as", "inasmuch", "until", "when", "whenever", "since", "while", "because", "before", "though"]
    @verb_list = ["vb", "vbd", "vbp", "vbz",] #, "vbg", "vbn" #participles, which I don't really want.
    @complementizer_count = 0
    @verb_count = 0
    @makes_things_worse_adjustment = 3 #if the selected part of speech would make things worse, multiply this by probability to make it harder to add the selected word



    @word_count = 0
    files = Dir.glob(File.join(*pathglob))
    files.each do |f|
      next if File.basename(f) == '.' or File.basename(f) == '..' or !lambdaFunc.call(File.basename(f))
      File.open(f).each do |line|
        #line = line.split(/[.?!]|$/) 
        [line].each do |sentence|
          split_sentence = sentence.strip().split(" ")
          word_two_back = ""
          word_back = ""
          split_sentence.each do |word|
            word.gsub("—", "")
            word = word.downcase.gsub(/[_\(\),]/, "") #—
            @word_count += 1

            unigram_counts[word] += 1
            bigram_inner_dict = bigram_counts[word_back].clone
            bigram_inner_dict[word] = bigram_inner_dict[word] +1
            bigram_counts[word_back] = bigram_inner_dict
            #trigram_counts[word_two_back][word_back][word] += 1
            trigram_one_step_inside = trigram_counts[word_two_back].clone
            trigram_two_steps_inside = trigram_one_step_inside[word_back].clone
            trigram_two_steps_inside[word] += 1
            trigram_one_step_inside[word_back] = trigram_two_steps_inside
            trigram_counts[word_two_back] = trigram_one_step_inside
            
            word_two_back = word_back
            word_back = word
          end
        end
      end
    end

    @trigramlm = {}
    @bigramlm = {}
    @bigramlm.default = {:tokencount => 0, :data => []}
    @trigramlm.default = @bigramlm
    @unigramlm = []

    trigram_counts.each do |word_two_back, trigram_counts_one_step_inside|
      trigram_LM_one_step_inside = {}
      outerCount = 0
      trigram_counts_one_step_inside.each do |word_back, trigram_counts_two_steps_inside|
        outerCount += 1
        count = 0
        trigram_LM_two_steps_inside = []
        trigram_counts_two_steps_inside.each do |word, myCount|
          count += myCount
          trigram_LM_two_steps_inside << [count, word]
        end
        trigram_LM_one_step_inside[word_back] = {}
        trigram_LM_one_step_inside[word_back].default = {:tokencount => 0, :data => []}
        trigram_LM_one_step_inside[word_back][:tokencount] = count
        trigram_LM_one_step_inside[word_back][:data] = trigram_LM_two_steps_inside
      end
      @trigramlm[word_two_back] = trigram_LM_one_step_inside
    end

    bigram_counts.each do |word_back, inner_hash|
      count = 0
      innerLM = []
      inner_hash.each do |word, myCount|
        count += myCount
        innerLM << [count, word]
      end
      @bigramlm[word_back] = {}
      @bigramlm[word_back].default = {:tokencount => 0, :data => []}
      @bigramlm[word_back][:tokencount] = count
      @bigramlm[word_back][:data] = innerLM
    end

    count = 0
    unigram_counts.each do |word, myCount|
      count += myCount
      @unigramlm << [count, word]
    end
    puts "done generating hashes"
    true
  end

  def check_verbs_and_complementizers(sentence_so_far, next_word, probability = 0.3 )
    #implements "very shallow parsing" on a sentence
    #if the sentence doesn't have N + 1 verbs for every N complementizers, 
    #   then, with some probability, return false if the next word if it doesn't resolve the imbalance.
    #   and return false with higher probability if the next word increases the imbalance
    #   in hopes of finding a word that satisfies the imbalance on the next go-round.

    tagged_sentence = @engtagger.add_tags( sentence_so_far.join(" ") )
    tagged_sentence_with_next_word = @engtagger.add_tags( (sentence_so_far + [next_word]).join(" ") )
    last_word_tag_stuff = tagged_sentence_with_next_word.split("> <")[-1].gsub(/^</, "").gsub(/>$/, "")
    last_word_POS = last_word_tag_stuff[0...last_word_tag_stuff.index(">")]
    last_word_content = last_word_tag_stuff[last_word_tag_stuff.index(">")+1 ... last_word_tag_stuff.index("<")]
    if tagged_sentence
      @verb_count = tagged_sentence.split("> <").select{ |e| @verb_list.include? e[0...e.index(">")] }.count
      @complementizer_count = tagged_sentence.split("> <").select{ |e| @complementizer_list.include?(e[0...e.index(">")]) || (e[0...e.index(">")] == "in" && @actual_IN_complementizers.include?(last_word_content) )}.count
    end
    #@verb_count = links.select{ |link| @verb_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size
    #@complementizer_count = links.select{ |link| @complementizer_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size

    if @verb_count == 0 && @complementizer_count == 0
      return true
    end

    puts [next_word, @verb_count, @complementizer_count, last_word_POS].join(" ") if @debug
    if @complementizer_list.include? last_word_POS
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif @verb_count > @complementizer_count + 1  #imbalance -- complementizer needed
        #accept, this fixes the imbalance!
        true
      elsif rand > probability * @makes_things_worse_adjustment #verb needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        true
      else 
        false
      end
    elsif @verb_list.include? last_word_POS
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif @verb_count < @complementizer_count + 1  #imbalance -- verb needed
        #accept, this fixes the imbalance!
        true
      elsif rand > probability * @makes_things_worse_adjustment #complementizer needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        true
      else 
        false
      end
    else
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif rand > probability #selected word doesn't fix the imbalance.
        #oh well, keep it.
        true
      else 
        #rejected!
        false
      end
    end
  end

  def next_word_bigrams(word_back)
    next_word_choices_stuff = @bigramlm[word_back]
    if rand < @unpathiness / Math.log( next_word_choices_stuff[:tokencount])
      puts "backing off to unigrams." if @debug
      next_word_choices_stuff[:data] = @unigramlm
      next_word_choices_stuff[:tokencount] = @word_count
    end
    next_word_choices_stuff
  end
  def next_word_trigrams(word_back, word_two_back)
    testthingy = @trigramlm[word_two_back]
    next_word_choices_stuff = testthingy[word_back] || {:tokencount => 0, :data => []}
    if rand < @unpathiness / Math.log( next_word_choices_stuff[:tokencount])
      puts "backing off to bigrams, aka smoothing." if @debug
      next_word_choices_stuff = next_word_bigrams(word_back)
    elsif ! next_word_choices_stuff 
      puts "backing off to bigrams, since trigrams returned nothing" if @debug
      next_word_choices_stuff = next_word_bigrams(word_back)
    end
    next_word_choices_stuff
  end


  def getnext_word(word_back, word_two_back)
    #returns the next word based on the word_back and word_two_back
    #  dumb wrapper around next_word_bigrams, !!Trigrams functions.
    #  i.e. doesn't do any parsing or anything.
    next_word_choices_stuff = next_word_trigrams(word_back, word_two_back)
    if ! next_word_choices_stuff 
      puts "backing off to bigrams, since trigrams returned nothing" if @debug
      next_word_choices_stuff = next_word_bigrams(word_back)
    end
    next_wordChoices = next_word_choices_stuff[:data].reverse
    tokencount = next_word_choices_stuff[:tokencount]

    next_word = nil
    myRand = rand(tokencount) + 1
    puts next_wordChoices.inspect if @debug
    puts "rand: #{myRand}, count: #{tokencount}, unpathiness: #{@unpathiness * 100}%" if @debug

    most_recent_world = nil
    next_wordChoices.each_with_index do | valword, index |
      val,word = valword
      if (myRand == val) 
        next_word = word
        break
      elsif (myRand > val) 
        next_word = most_recent_world 
        break     
      elsif index == (next_wordChoices.size) - 1
        next_word = word
        break
      end
      most_recent_world = word
    end
    next_word
  end

  def get_phrase (opts = {})
   o = { #set defaults
      :maxLen => 30, # if you set maxLen to 0, there is no maxLen
      :unpathiness => 0.0, #TODO: Remember what this does.
      :word_two_back => "",
      :word_back => "", 
      :debug => false,
      :engtagger => false, #TODO: Set to true, see if sentences are more coherent.
      :guaranteeParse => false,
   }.merge(opts)
		@unpathiness = o[:unpathiness]
    maxLen = o[:maxLen]
    word_two_back = o[:word_two_back]
    word_back = o[:word_back]
    @debug = o[:debug]
    useEngtagger = o[:engtagger]
    use_linkparser_to_validate_sentences = o[:guaranteeParse]  #should we return only parse-able sentences?
    puts "going to use engtagger" if @debug && useEngtagger

    so_far = [word_two_back, word_back]
    endOfSentence = false

    loop do
      next_word = getnext_word(word_back, word_two_back)
      if next_word
        # conditions under which we reject a word and go back to picking another one.
        if useEngtagger && ! check_verbs_and_complementizers(so_far, next_word)
          puts "trying to resolve verb-complementizer imbalance, rejecting \"" + next_word.to_s + "\"" if @debug
        elsif false #if the word is off topic
          #given a topic, 
          #check if an "on topic" word could come next -- with 10% chance, choose it.          
          
        else
          so_far << next_word
          puts so_far.join(" ") if @debug
          word_two_back = word_back
          word_back = next_word
          break if next_word == "" || (maxLen != 0 && so_far.length >= maxLen) 
        end
      else
        break
      end
    end
    sentence = so_far.join(" ").strip

    if !use_linkparser_to_validate_sentences
      sentence
    else
      require 'linkparser'
      sentence = so_far.join(" ").strip
      @linkparser = LinkParser::Dictionary.new
      result = @linkparser.parse(sentence)
      if result.linkages != []
        sentence
      else
        puts "ehhhhh, sentence didn't parse, trying again!" if @debug
        get_phrase(opts) #if the sentence doesn't parse, throw it out and start again.
      end
    end
  end


  attr_reader :trigramlm, :bigramlm, :engtagger, :verb_count, :complementizer_count
  #accessor methods for debugging, etc.
end

@n = LanguageModel.new(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda{|filename| filename == "SCALIA.txt"})
puts @n.get_phrase({:debug => true, :engtagger => true})
