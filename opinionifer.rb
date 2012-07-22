# encoding: UTF-8
require 'fileutils'

def isBeginningOfOpinion(file, filename)
  beginning = file.readlines[0..20]
  beginning.select!{|line| line != "" && ! /\d/.match(line)}
  scotusLine = beginning.select {|line| !line.index("SUPREME COURT OF THE UNITED STATES").nil?} 
  opinionLine = beginning.select {|line| !line.index("Opinion of").nil?} + beginning.select {|line| !line.index("concurring").nil?} +  beginning.select {|line| !line.index("dissenting").nil?} 
  if opinionLine.size >= 1
    justice = opinionLine.first.gsub("Opinion of ", "").chomp
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

def formatOpinion(opinion)
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
          !line.index("v.").nil? || line.match(/^[A-Z., ]+$/) || !line.index("——————").nil? ||\
          !line.index("").nil? || line == ("Per Curiam") || line.match(/No\. \d+–\d+. Decided [A-Za-z]+ \d+, \d+/) || isFootnotes
        newPage << line
      end
      if !line.index("——————").nil? || isFootnotes
        isFootnotes = true
        footnotes << line
      end
    end
    newOpinion << newPage.join(" ") #TODO split on punctuation and join('\n') 
    #TODO: Check if last word of line1 and first word of line 2 don't exist in dictionary but combined, if they do. E.g. ren\ndered => rendere
  end
  newOpinion += footnotes
  newOpinion.join("\n")
end

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
          justice = justice.split(",")[0].chomp()
        else
          justice = "only"
        end
        opinion << f.read() if index == pages.size-1
        previousJustice = orderOfJustices[-2] || "per curiam" 
        opinionFilepath = File.join("opinions", caseFolder.split("/")[1], caseFolder.split("/")[2], previousJustice) + ".txt"
        rawOpinionFilepath = File.join("opinions", caseFolder.split("/")[1], caseFolder.split("/")[2], previousJustice) + ".raw.txt"
        FileUtils.mkdir_p(File.dirname(opinionFilepath)) if ! File.exists? File.dirname(opinionFilepath)
        File.open(opinionFilepath, "w") {|f| f.write(formatOpinion(opinion)) }
        File.open(rawOpinionFilepath, "w") {|f| f.write(opinion.join("\n")) }
        opinion = []
      end
      opinion << f.read()
    end
    puts caseFolder + ": " + endOfMajorityOpinionPages.inspect + "; " + orderOfJustices.inspect
    #now we know where the
  end
end
