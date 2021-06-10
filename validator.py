#!/usr/bin/env python3

import requests
import json
from mqaMetrics import metrics
from xml.etree import ElementTree
import argparse

URL_EDP = 'https://data.europa.eu/api/mqa/shacl/validation/report'
HEADERS = {'content-type': 'application/rdf+xml'}

def valResult(d):
  if 'sh:conforms' in d:
    return d['sh:conforms']
  for k in d:
    if isinstance(d[k], list):
      for i in d[k]:
        #print(i)
        if 'sh:conforms' in i:
            return i['sh:conforms']

def getTags(filename):
  # Get the namaspaces of RDF file
  my_ns = dict([node for _, node in ElementTree.iterparse(filename, events=['start-ns'])])
  #print(my_ns)

  tree = ElementTree.parse(filename)
  tagList=[]
  for node in tree.iter():
    tag = node.tag
    #print(tag)
    ns1 = tag[tag.find("{")+1:tag.find("}")]
    #print("ns1 "+ns1)
    ns2 = tag[tag.find("{"):tag.find("}")+1]
    #print("ns2 "+ns2)
    for key, value in my_ns.items():
      if ns1 == value:
        #print(key)
        newTag=tag.replace(ns2, key+":")
        #print(newTag)
        if newTag != "rdf:RDF":
          try:
            tagList.index(newTag)
          except ValueError:
            tagList.append(newTag)
      
  print('RDF vocabulary detected:')
  print(tagList)
  return tagList

def mqaStats(metrics,tags, res):
  #print('metrics')
  #print(metrics)
  #print('tags')
  #print(tags)
  score = 0
  for t in tags:
    for m in metrics:
      if t == m["Metric"]:
        score = score + m["Weight"]
        print("** "+ t + " - " + str(m["Weight"]))
  if res:
    score = score + 30
    print('** SHACL validation - 30')
  else:
    print('** SHACL validation - 0')
  print("Overall scoring: "+str(score))
  if score in range(351,406):
    print("Rating: Excellent")
  if score in range(221,351):
    print("Rating: Good")
  if score in range(121,221):
    print("Rating: Sufficient")
  if score in range(0,121):
    print("Rating: Bad")

def main():
  
  parser = argparse.ArgumentParser(description='EDP validator CLI')
  parser.add_argument('-f', '--file', type=str, required=True, help='RDF file to be validated')
  args = parser.parse_args()

  try:
    rdfFile = open(args.file, "r")
  except Exception as e:
    raise SystemExit(e)
  else:
    print(args.file, 'opened successfully')

  with rdfFile:
    try:
      payload = rdfFile.read().replace("\n", " ")
      r_edp = requests.post(URL_EDP, data=payload, headers=HEADERS)
      r_edp.raise_for_status()
    except requests.exceptions.HTTPError as err:
      raise SystemExit(err)
    print('EDP request status: ', r_edp.status_code)
    #print(r_edp.text)
    report = json.loads(r_edp.text)
    res = valResult(report)
    print("EDP validation result: ", res)
    
    tags = getTags(args.file)
    print('EDP quality scoring:')
    mqaStats(metrics, tags, res)

if __name__ == "__main__":
    main()
