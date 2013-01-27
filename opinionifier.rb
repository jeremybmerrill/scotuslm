# encoding: UTF-8
require 'fileutils'
require './lib/lineCombiner/lineCombiner.rb'
require 'punkt-segmenter'

class Opinionifier

  def initialize
  end


  def get_justice_name(opinion_line)
    justice = opinion_line.first.gsub(/Opinion\sof\s|Statement\sof\s/, "").strip

    if justice.empty?
      return nil
    elsif justice != "the Court"
      justice = justice.split(" ")[0].gsub(",","")
    end
    return justice
  end

  def is_beginning_of_opinion(file, filename) #TODO: rename this method
    beginning = file.readlines[0..20]
    beginning.select!{|line| line != "" && ! /\d/.match(line)}
    scotus_line = beginning.select {|line| !line.index("SUPREME COURT OF THE UNITED STATES").nil?} 
    opinion_line = beginning.select {|line| !line.index("Opinion of").nil?} + beginning.select {|line| !line.index("concurring").nil?} +  beginning.select {|line| !line.index("dissenting").nil?} 
    
    if !opinion_line.empty? && !opinion_line.nil?
      justice = get_justice_name(opinion_line)
      #if justice.nil?
      #  puts opinion_line.inspect
      #  justice = get_justice_name( beginning[ beginning.index(opinion_line) + 1]  ) #try the next line
      #end
    end

    underscore_line = beginning.select {|line| !line.index("__________").nil?}
    case_line = beginning.select {|line| !line.index("v.").nil?}

    is_syllabus = !beginning.select {|line| !line.index("Syllabus").nil?}.empty?

    is_beginning = !scotus_line.empty? && !opinion_line.empty? && !underscore_line.empty? && !case_line.empty?
    if is_beginning && false
      puts scotus_line.inspect
      puts opinion_line.inspect
      puts underscore_line.inspect
      puts case_line.inspect
      puts "\n\n"
    end

    [is_beginning, justice, is_syllabus]
  end

  def format_opinion(opinion, opinion_name, line_combiner = LineCombiner.new)
    #cut out page numbers, etc.
    #remove a line if it is:
    # => in all caps
    # => only a number (Arabic or Roman)
    # => begins with "Cite as:"
    # => is blank
    # => is all dashes
    # => is "v."
    new_opinion = []
    footnotes = []
    opinion.each do |page|
      new_page = []
      is_footnotes = false
      page.split("\n").each do |line|
        unless line == "" || /^\d+$/.match(line) || line.match(/^[0-9]+$/) || line.match(/Cite as: .*/) || \
            !line.index("________").nil? || !line.index("SUPREME COURT OF THE UNITED STATES").nil? || \
            !line.index("Opinion of").nil? || !line.index("Statement of").nil? || !line.match(/^[A-Z ,.]+ (concurring|dissenting)$/).nil?  ||\
            line.match(/^v.$/) || line.match(/^[A-Z., ]+$/) || !line.index("——————").nil? ||\
            !line.index("").nil? || line == ("Per Curiam") || line.match(/No\. \d+–\d+. Decided [A-Za-z]+ \d+, \d+/) ||\
            line.match(/No\. \d+\d+ \[[A-Za-z]+ \d+, \d+\]/) || is_footnotes
          new_page << line
        end
        if !line.index("——————").nil? || is_footnotes
          is_footnotes = true
          footnotes << line
        end
      end

      new_page_combined = new_page.reduce([]) do |lines, next_line|
        if !lines.empty? && !next_line.nil? && !next_line.strip.empty?
          w1 = lines[-1].split(" ")[-1]
          if w1.nil?
            lines + [next_line.strip]
          else
            raise AsdfError if w1.include? " "
            w2 = next_line.strip.split(" ")[0]
            w2suffix = ""
            if w2.include? ("'s")
              w2 = w2.split("'s")[0]
              w2suffix = "'s"
            end
            rest_of_next_line = next_line.strip.split(" ")[1..-1]
            raise AsdfError if w2.length == 0
            if w2.match(/[A-Z][a-z]+/) #if w2 is capitalized, don't combine.
              lines + [next_line.strip]
            elsif line_combiner.safe_to_combine?(w1, w2) 
              puts "combined: " + w1 + w2
              lines[-1] = lines[-1].split(" ")[0..-2] + [w1 + w2] #add w2 to the end of w1
              lines + [rest_of_next_line.join(" ").strip]
            else
              lines + [next_line.strip]
            end
          end
        else
          lines + [next_line.strip]
        end
      end

      new_opinion << new_page_combined.join(" ") #TODO split on punctuation and join('\n') 
    end
    #new_opinion += footnotes
    new_opinion = new_opinion.join(" ").gsub("[", "").gsub("]", "").gsub("(","").gsub("­\n","").gsub("­ ", "").gsub(")", "").gsub(" . . .", "...").gsub(/“|”/, '"')
    if new_opinion.size > $largest[0]
      $largest = [new_opinion.size, opinion_name] 
      puts new_opinion.size
    end
    unless new_opinion.nil? || new_opinion.empty?
      tokenizer = Punkt::SentenceTokenizer.new(new_opinion)
      lines = tokenizer.sentences_from_text(new_opinion, :output => :sentences_text).join("\n")
    end
  end


  def format_all_opinions(line_combiner = LineCombiner.new)
    year_folders = Dir["txts/*"]
    year_folders.each do |folder|
      cases = Dir.glob("#{folder}/*")
      cases.each do |case_folder|
        pages = Dir.glob("#{case_folder}/*")
        end_of_majority_opinion_pages = []
        order_of_justices = []
        pages.each do |filename|
          number = filename.split("_")[-1].split(".")[0]
          rest = filename.split("_")[0..-2].join("") 
          if number.length == 3
            new_number = number
          elsif number.length == 2
            new_number = "0" + number
          elsif number.length == 1
            new_number = "00" + number
          else
            puts number, filename
            raise AsdfError
          end
          newFilename = [rest, "_", new_number, ".txt"].join("")
          FileUtils.move(filename, newFilename) unless filename == newFilename
        end
        opinion = []
        ordered_pages = Dir.glob("#{case_folder}/*").sort
        ordered_pages.each_with_index do |filename, index|
          page_number = filename[(filename.rindex("_")+1)..-5].to_i
          #outputFilename = filename.gsub("txt", "opinion")
          f = File.open(filename)
          is_beginning = is_beginning_of_opinion(f, filename)
          f.close()
          f = File.open(filename)
          if is_beginning[2] && order_of_justices == []
            order_of_justices << "syllabus"
          end
          if is_beginning[0] || index == pages.size-1
            puts "asfd" if index == cases.size-1
            justice = is_beginning[1]
            end_of_majority_opinion_pages.push(page_number)
            order_of_justices.push(justice)
            if justice
              begin
                justice = justice.split(",")[0].strip()
              rescue NoMethodError
                puts justice + " failed on splitting and stripping"
              end
            else
              justice = "only"
            end
            opinion << f.read() if index == pages.size-1
            previous_justice = order_of_justices[-2] || "per curiam" 
            opinion_filepath = File.join("opinions", case_folder.split("/")[1], case_folder.split("/")[2], previous_justice) + ".txt"
            raw_opinion_filepath = File.join("opinions", case_folder.split("/")[1], case_folder.split("/")[2], previous_justice) + ".raw.txt"
            FileUtils.mkdir_p(File.dirname(opinion_filepath)) if ! File.exists? File.dirname(opinion_filepath)
            #begin
              File.open(opinion_filepath, "w") {|f| f.write(format_opinion(opinion, opinion_filepath, line_combiner)) }
            #rescue NoMethodError
              #puts "failed: " + filename
            #end
            File.open(raw_opinion_filepath, "w") {|f| f.write(opinion.join("\n")) }
            opinion = []
          end
          opinion << f.read()
        end
        puts case_folder + ": " + end_of_majority_opinion_pages.inspect + "; " + order_of_justices.inspect
        #now we know where the
      end
    end
  end
end
$largest = [0, ""]
o = Opinionifier.new()
o.format_all_opinions()
puts $largest
