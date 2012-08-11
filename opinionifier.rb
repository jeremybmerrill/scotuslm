# encoding: UTF-8
require 'fileutils'
require './lib/lineCombiner/lineCombiner.rb'
require 'punkt-segmenter'

def isBeginningOfOpinion(file, filename)
  beginning = file.readlines[0..20]
  beginning.select!{|line| line != "" && ! /\d/.match(line)}
  scotusLine = beginning.select {|line| !line.index("SUPREME COURT OF THE UNITED STATES").nil?} 
  opinionLine = beginning.select {|line| !line.index("Opinion of").nil?} + beginning.select {|line| !line.index("concurring").nil?} +  beginning.select {|line| !line.index("dissenting").nil?} 
  if opinionLine.size >= 1
    justice = opinionLine.first.gsub("Opinion of ", "").strip
    if justice != "the Court"
      justice = justice.split(" ")[0].gsub(",","")
    end
  end
  underscoreLine = beginning.select {|line| !line.index("__________").nil?}
  caseLine = beginning.select {|line| !line.index("v.").nil?}

  isSyllabus = !beginning.select {|line| !line.index("Syllabus").nil?}.empty?

  isBeginning = !scotusLine.empty? && !opinionLine.empty? && !underscoreLine.empty? && !caseLine.empty?
  if isBeginning && false
    puts scotusLine.inspect
    puts opinionLine.inspect
    puts underscoreLine.inspect
    puts caseLine.inspect
    puts "\n\n"
  end

  [isBeginning, justice, isSyllabus]
end

def formatOpinion(opinion, opinionName, lineCombiner = LineCombiner.new)
  #cut out page numbers, etc.
  #remove a line if it is:
  # => in all caps
  # => only a number (Arabic or Roman)
  # => begins with "Cite as:"
  # => is blank
  # => is all dashes
  # => is "v."
  newOpinion = []
  footnotes = []
  opinion.each do |page|
    newPage = []
    isFootnotes = false
    page.split("\n").each do |line|
      unless line == "" || /^\d+$/.match(line) || line.match(/^[0-9]+$/) || line.match(/Cite as: .*/) || \
          !line.index("________").nil? || !line.index("SUPREME COURT OF THE UNITED STATES").nil? || \
          !line.index("Opinion of").nil? || !line.match(/^[A-Z ,.]+ (concurring|dissenting)$/).nil?  ||\
          line.match(/^v.$/) || line.match(/^[A-Z., ]+$/) || !line.index("——————").nil? ||\
          !line.index("").nil? || line == ("Per Curiam") || line.match(/No\. \d+–\d+. Decided [A-Za-z]+ \d+, \d+/) ||\
          line.match(/No\. \d+\d+ \[[A-Za-z]+ \d+, \d+\]/) || isFootnotes
        newPage << line
      end
      if !line.index("——————").nil? || isFootnotes
        isFootnotes = true
        footnotes << line
      end
    end

    newPageCombined = newPage.reduce([]) do |lines, nextLine|
      if !lines.empty? && !nextLine.nil? && nextLine.strip != ""
        w1 = lines[-1].split(" ")[-1]
        raise AsdfError if w1.include? " "
        w2 = nextLine.strip.split(" ")[0]
        w2suffix = ""
        if w2.include? ("'s")
          w2 = w2.split("'s")[0]
          w2suffix = "'s"
        end
        restOfNextLine = nextLine.strip.split(" ")[1..-1]
        raise AsdfError if w2.length == 0
        if w2.match(/[A-Z][a-z]+/) #if w2 is capitalized, don't combine.
          lines + [nextLine.strip]
        elsif lineCombiner.safeToCombine?(w1, w2) 
          puts "combined: " + w1 + w2
          lines[-1] = lines[-1].split(" ")[0..-2] + [w1 + w2] #add w2 to the end of w1
          lines + [restOfNextLine.strip]
        else
          lines + [nextLine.strip]
        end
      else
        lines + [nextLine.strip]
      end
    end

    newOpinion << newPageCombined.join(" ") #TODO split on punctuation and join('\n') 
    #TODO: Check if last word of line1 and first word of line 2 don't exist in dictionary but combined, if they do. E.g. ren\ndered => rendere
  end
  #newOpinion += footnotes
  newOpinion = newOpinion.join(" ").gsub("[", "").gsub("]", "").gsub("(","").gsub(")", "").gsub(" . . .", "...")
  if newOpinion.size > $largest[0]
    $largest = [newOpinion.size, opinionName] 
    puts newOpinion.size
  end
  tokenizer = Punkt::SentenceTokenizer.new(newOpinion)
  lines = tokenizer.sentences_from_text(newOpinion, :output => :sentences_text).join("\n")
end


def formatAllOpinions(lineCombiner = LineCombiner.new)
  yearFolders = Dir["txts/*"]
  yearFolders.each do |folder|
    cases = Dir.glob("#{folder}/*")
    cases.each do |caseFolder|
      pages = Dir.glob("#{caseFolder}/*")
      endOfMajorityOpinionPages = []
      orderOfJustices = []
      pages.each do |filename|
        number = filename.split("_")[-1].split(".")[0]
        rest = filename.split("_")[0..-2].join("") 
        if number.length == 3
          newNumber = number
        elsif number.length == 2
          newNumber = "0" + number
        elsif number.length == 1
          newNumber = "00" + number
        else
          puts number, filename
          raise AsdfError
        end
        newFilename = [rest, "_", newNumber, ".txt"].join("")
        FileUtils.move(filename, newFilename) unless filename == newFilename
      end
      opinion = []
      orderedPages = Dir.glob("#{caseFolder}/*").sort
      orderedPages.each_with_index do |filename, index|
        pageNumber = filename[(filename.rindex("_")+1)..-5].to_i
        #outputFilename = filename.gsub("txt", "opinion")
        f = File.open(filename)
        isBeginning = isBeginningOfOpinion(f, filename)
        f.close()
        f = File.open(filename)
        if isBeginning[2] && orderOfJustices == []
          orderOfJustices << "syllabus"
        end
        if isBeginning[0] || index == pages.size-1
          puts "asfd" if index == cases.size-1
          justice = isBeginning[1]
          endOfMajorityOpinionPages.push(pageNumber)
          orderOfJustices.push(justice)
          if justice
            justice = justice.split(",")[0].strip()
          else
            justice = "only"
          end
          opinion << f.read() if index == pages.size-1
          previousJustice = orderOfJustices[-2] || "per curiam" 
          opinionFilepath = File.join("opinions", caseFolder.split("/")[1], caseFolder.split("/")[2], previousJustice) + ".txt"
          rawOpinionFilepath = File.join("opinions", caseFolder.split("/")[1], caseFolder.split("/")[2], previousJustice) + ".raw.txt"
          FileUtils.mkdir_p(File.dirname(opinionFilepath)) if ! File.exists? File.dirname(opinionFilepath)
          begin
            File.open(opinionFilepath, "w") {|f| f.write(formatOpinion(opinion, opinionFilepath, lineCombiner)) }
          rescue NoMethodError
            puts filename
          end
          File.open(rawOpinionFilepath, "w") {|f| f.write(opinion.join("\n")) }
          opinion = []
        end
        opinion << f.read()
      end
      puts caseFolder + ": " + endOfMajorityOpinionPages.inspect + "; " + orderOfJustices.inspect
      #now we know where the
    end
  end
end
$largest = [0, ""]
formatAllOpinions()
puts $largest
