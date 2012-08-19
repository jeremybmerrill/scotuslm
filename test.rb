load './lm.rb'
require 'linkparser'

TIMES= 10000

def colorize(text, color_code)
  "#{color_code}#{text}\e[0m"
end

def red(text); colorize(text, "\e[31m"); end
def green(text); colorize(text, "\e[32m"); end


l = LanguageModel.new(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda{|filename| filename == "SCALIA.txt"})
linkparser = LinkParser::Dictionary.new()

yes_tagger_count = 0
TIMES.times do 
  sent = l.getPhrase({:engtagger => true})
  result = linkparser.parse(sent)
  puts green(sent + ", " + result.linkages.to_s)
  if result.linkages != []
    yes_tagger_count += 1 
  end
end

#puts "------------------" * 4

no_tagger_count = 0
TIMES.times do
  sent = l.getPhrase({:engtagger => false})
  result = linkparser.parse(sent)
  #puts green(sent + ", " + result.linkages.to_s)
  if result.linkages != []
    no_tagger_count += 1 
  end
end

puts "yes: " + yes_tagger_count.to_s
puts "no: " + no_tagger_count.to_s