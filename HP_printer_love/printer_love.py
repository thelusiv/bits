#!/usr/bin/python

# This program gets random one-line quotes from a text file, formats them
# to fit on a 20-characters-per-line display, and then calls another script
# to send the message to any number of printers. 

# Put the IP address(es) if your HP printer(s) here.
printers = ["192.168.100.5"]

import sys, os, random, time

def getquote(filename="quotes.txt"):
  """
  Get a random line from a text file named quotes.txt and return it.
  """
  random.seed(time.time())
  quotes_file = open(filename)
  lines = quotes_file.readlines()
  return random.choice(lines)

def mywrap(message=" ~ I love you! ~~"):
  """
  Simple, probably inefficient, function to pad string with spaces so that
  lines come out as 20 chars long. Perfect for a HP Printer display.
  A few little extra features: If you put " ~ " it will force a line break
  between the two words it separates. If you put " ~~ " between two words,
  the words on the current line will be centered on that line.
  """
  result = ""
  line = ""
  if len(message) == 80:
    return message
  for word in message.split(' '):
    linelen = len(line)
    if word == "~":
      result += line + ' '*(20-linelen)
      line = ""
    elif word == "~~":
      result += line.center(20)
      line = ""
    elif linelen + len(word) == 20:
      result += line + word
      line = ""
    elif linelen + len(word) > 20:
      result += line + ' '*(20-linelen)
      line = word + ' '
    elif linelen + len(word) <= 19:
      line += word + ' '
  if line != "":
    result += line
  return result.rstrip()


# main program
print sys.argv


message = mywrap(getquote())
if len(message) > 80:
  print "WARNING: This message is longer than the display on the printer."

print "Message: %s" % message

for ip in printers:
  command = "perl hpsetdisp.pl %s \"%s\"" % (ip, message)
  #os.system(command)
  print "Sent to printer at %s" % ip


